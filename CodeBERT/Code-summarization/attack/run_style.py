import os

os.system("python attack_style.py \
    --output_dir=../saved_models \
    --model_type=roberta \
    --model_name_or_path microsoft/codebert-base \
    --dev_filename=../../../Data/Code-summarization/test_sampled.jsonl \
    --csv_store_path1 ../result/codebert_sum_style.csv \
    --base_model=../../../Model/CodeBERT-mlm \
    --block_size 512 \
    --eval_batch_size 64 \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --seed 123456  2>&1")

