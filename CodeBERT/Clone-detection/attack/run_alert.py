import os

os.system("python attack_alert.py \
    --output_dir=../saved_models \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --csv_store_path ../result/codebert_clone_alert.csv \
    --base_model=microsoft/codebert-base-mlm \
    --use_ga \
    --eval_data_file=../../../Data/Clone-detection/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 256 \
    --seed 123456")

