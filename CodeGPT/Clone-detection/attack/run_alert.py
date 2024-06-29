import os

os.system("python attack_alert.py \
    --output_dir=../saved_models \
    --model_type=gpt2 \
    --tokenizer_name=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --model_name_or_path=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --base_model=microsoft/codebert-base-mlm \
    --csv_store_path ../result/codegpt_clone_alert.csv \
    --config_name=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --use_ga \
    --eval_data_file=../../../Data/Clone-detection/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 64 \
    --seed 123456  2>&1")

