import os

os.system("python attack_wir.py \
    --output_dir=../saved_models \
    --model_type=gpt2 \
    --tokenizer_name=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --model_name_or_path=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --csv_store_path ../result/codegpt_clone_wir.csv \
    --config_name=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --eval_data_file=../../../Data/Clone-detection/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 64 \
    --seed 123456")
