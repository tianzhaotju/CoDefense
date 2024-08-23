import os

os.system("python attack_alert.py \
    --output_dir=../saved_models \
    --model_type=gpt2 \
    --model_name_or_path microsoft/CodeGPT-small-java-adaptedGPT2 \
    --base_model=microsoft/codebert-base-mlm \
    --dev_filename=../../../Data/Code-summarization/test_sampled.jsonl \
    --load_model_path=../saved_models/checkpoint-best-bleu/pytorch_model.bin \
    --csv_store_path ../result/codegpt_sum_alert.csv \
    --use_ga \
    --eval_batch_size 32 \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --seed 123456")

