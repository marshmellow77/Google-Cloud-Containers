import argparse

import torch
import torch_xla
import torch_xla.core.xla_model as xm
import torch_xla.distributed.xla_multiprocessing as xmp
from datasets import load_dataset
from peft import LoraConfig, TaskType
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    TrainingArguments,
)
from trl import SFTTrainer


def train_model(args):
    raw_dataset = load_dataset("databricks/databricks-dolly-15k", split="train")

    def format_dolly(sample):
        instruction = f"### Instruction\n{sample['instruction']}"
        context = (
            f"### Context\n{sample['context']}" if len(sample["context"]) > 0 else None
        )
        response = f"### Answer\n{sample['response']}"
        # join all the parts together
        prompt = "\n\n".join(
            [i for i in [instruction, context, response] if i is not None]
        )
        sample["text"] = prompt
        return sample

    # apply prompt template
    format_dataset = raw_dataset.map(
        format_dolly, remove_columns=list(raw_dataset.features)
    )

    # Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    tokenizer.pad_token = tokenizer.eos_token

    # Scale learning rate to num cores
    lr = args.lr * xm.xrt_world_size()
    device = xm.xla_device()

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, torch_dtype=torch.bfloat16
    )
    lora_config = LoraConfig(
        r=16,
        target_modules=["q_proj", "v_proj"],
        task_type=TaskType.CAUSAL_LM,
        lora_alpha=32,
        lora_dropout=0.05,
    )

    # Define training arguments
    training_args = TrainingArguments(
        output_dir="output",
        per_device_train_batch_size=args.train_batch_size,
        per_device_eval_batch_size=args.test_batch_size,
        learning_rate=lr,
        gradient_accumulation_steps=2,  # number of steps before performing a backward/update pass
        gradient_checkpointing=True,  # use gradient checkpointing to save memory
        optim="adamw_torch_fused",
        num_train_epochs=args.num_epochs,
        logging_strategy="steps",
        logging_steps=10,
        bf16=True,
    )

    # Initialize our Trainer
    trainer = SFTTrainer(
        model=model,
        peft_config=lora_config,
        args=training_args,
        dataset_text_field="text",
        packing=True,
        train_dataset=format_dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
    )
    # Train the model
    trainer.train()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_id", default="facebook/opt-125m", type=str)
    parser.add_argument("--num_cores", default=8, type=int)
    parser.add_argument("--num_epochs", default=3, type=int)
    parser.add_argument("--train_batch_size", default=16, type=int)
    parser.add_argument("--lr", default=3e-4, type=float)
    args = parser.parse_args()
    return args


def _mp_fn(index, args):
    torch.set_default_dtype(torch.bfloat16)
    train_model(args)


if __name__ == "__main__":
    args = parse_args()
    xmp.spawn(_mp_fn, args=(args,), nprocs=args.num_cores)
