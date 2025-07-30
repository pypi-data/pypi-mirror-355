import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F

from typing import Dict, List
from huggingface_hub import hf_hub_download

class T5ForDualTask(nn.Module):
    def __init__(
        self,
        model_name: str = "google/flan-t5-base",
        use_lora: bool = False,
        lora_r: int = 8,
        lora_alpha: int = 32,
        lora_dropout: float = 0.1,
        lora_target_modules: List[str] = ["q", "v"],
    ):
        super().__init__()
        from transformers import T5ForConditionalGeneration
        self.model = T5ForConditionalGeneration.from_pretrained(model_name).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
        self.use_lora = use_lora

        self.classifier = nn.Linear(
            self.model.config.d_model, 2
        )  # DELETE(1) and KEEP(0)

        try:
            # Attempt to load the classifier weights from the Hugging Face Hub
            classifier_path = hf_hub_download(
                repo_id=model_name,
                filename="classifier.pt"
            )
            self.classifier.load_state_dict(
                torch.load(classifier_path, weights_only=True)
            )
            self.classifier.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
            self.classifier.eval()  # Set to eval mode
            print("Successfully loaded classifier weights from Hugging Face Hub.")
        except Exception as e:
            print(f"Error download/load classifier weights: {e}")

        if use_lora:
            from peft import get_peft_model, LoraConfig, TaskType
            lora_config = LoraConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                r=lora_r,
                lora_alpha=lora_alpha,
                lora_dropout=lora_dropout,
                target_modules=lora_target_modules,
            )
            self.model = get_peft_model(self.model, lora_config)

    def forward_delete(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor = None,
        span_mask: torch.Tensor = None,
        triple_spans: torch.Tensor = None,
    ) -> Dict[str, torch.Tensor]:
        encoder_outputs = self.model.encoder(
            input_ids=input_ids, attention_mask=attention_mask, return_dict=True
        )
        cls_hidden_state = encoder_outputs.last_hidden_state

        all_logits = []
        all_labels = []
        for i in range(input_ids.size(0)):
            span = triple_spans[i]  # list of (start, end) tuples for sample i
            masked_span = span[span_mask[i]]
            triple_reps = []
            for start, end in masked_span:
                # Obtain the embedding for the triple span by averaging token embeddings.
                span_emb = cls_hidden_state[i, start:end+1, :].mean(dim=0)  # TODO: try some new methods
                triple_reps.append(span_emb)
            # Stack the triples representations and classify each.
            if not triple_reps:
                continue
            triple_reps = torch.stack(triple_reps, dim=0)
            logits = self.classifier(triple_reps)
            all_logits.append(logits)
            if labels is not None:
                masked_labels = labels[i][span_mask[i]]
                all_labels.append(masked_labels)

        all_logits = torch.cat(all_logits, dim=0)
        outputs = {"logits": all_logits}

        if labels is not None:
            all_labels = torch.cat(all_labels, dim=0)
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(all_logits, all_labels)
            outputs["loss"] = loss

        return outputs
    
    def forward_delete_maskBIO(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor = None,
        span_mask: torch.Tensor = None,
        triple_spans: torch.Tensor = None,
    ) -> Dict[str, torch.Tensor]:
        encoder_outputs = self.model.encoder(
            input_ids=input_ids, attention_mask=attention_mask, return_dict=True
        )
        cls_hidden_state = encoder_outputs.last_hidden_state

        B, L, H = cls_hidden_state.size()

        batch_idx, start_idx, end_idx, span_labels = [], [], [], []

        for b in range(B):
            keep = span_mask[b].nonzero(as_tuple=False).squeeze(1)
            if keep.numel() == 0:
                continue
            spans = triple_spans[b].detach().clone()[keep]
            start, end = spans[:, 0], spans[:, 1]
            k = start.size(0)

            batch_idx.append(torch.full((k,), b, device=cls_hidden_state.device))
            start_idx.append(start)
            end_idx.append(end)

            if labels is not None:
                span_labels.append(labels[b][keep])
            
        if not batch_idx:
            empty_tensor = torch.zeros((0, 2), device=cls_hidden_state.device)
            return {"logits": empty_tensor}
        
        batch_idx = torch.cat(batch_idx, dim=0)
        start_idx = torch.cat(start_idx, dim=0)
        end_idx = torch.cat(end_idx, dim=0)
        if labels is not None:
            span_labels = torch.cat(span_labels, dim=0)
        
        cumsum = torch.cumsum(cls_hidden_state, dim=1)
        cumsum = F.pad(cumsum, (0, 0, 1, 0))

        span_sum = cumsum[batch_idx, end_idx + 1] - cumsum[batch_idx, start_idx]
        span_len = (end_idx - start_idx + 1).unsqueeze(1)
        span_repr = span_sum / span_len

        logits = self.classifier(span_repr)
        outputs = {"logits": logits}
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, 2), span_labels.view(-1))
            outputs["loss"] = loss
        return outputs

    def forward_insert(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        decoder_input_ids: torch.Tensor,
        labels: torch.Tensor = None,
    ) -> Dict[str, torch.Tensor]:
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            labels=labels,
            return_dict=True,
        )

        return {"loss": outputs.loss, "logits": outputs.logits}

    def generate(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor, **kwargs
    ) -> torch.Tensor:
        return self.model.generate(
            input_ids=input_ids, attention_mask=attention_mask, **kwargs
        )


# def main():
#     # Example usage
#     model = T5ForDualTask(model_name="sqlinn/DiscoSG-Refiner-Large-t5-only", use_lora=False)
#     input_ids = torch.randint(0, 1000, (2, 10))  # Dummy input
#     attention_mask = torch.ones((2, 10), dtype=torch.long)  # Dummy attention mask
#     labels = torch.randint(0, 2, (2, 10))  # Dummy labels
#     span_mask = torch.tensor([[1, 0, 1, 0, 1, 0, 1, 0, 1, 0], [1, 1, 0, 0, 1, 1, 0, 0, 1, 1]])
#     triple_spans = torch.tensor([[(0, 2), (4, 6)], [(0, 3), (4, 5)]])

#     outputs = model.forward_delete(
#         input_ids=input_ids,
#         attention_mask=attention_mask,
#         labels=labels,
#         span_mask=span_mask,
#         triple_spans=triple_spans,
#     )
#     print(outputs)

# if __name__ == "__main__":
#     main()