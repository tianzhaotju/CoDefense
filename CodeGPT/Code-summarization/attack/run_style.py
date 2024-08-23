import os

os.system("python attack_style.py \
    --output_dir=../saved_models \
    --model_type=gpt2 \
    --model_name_or_path microsoft/CodeGPT-small-java-adaptedGPT2 \
    --dev_filename=../../../Data/Code-summarization/test_sampled.jsonl \
    --csv_store_path1 ../result/codegpt_sum_style.csv \
    --load_model_path=../saved_models/checkpoint-best-bleu/pytorch_model.bin \
    --eval_batch_size 64 \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --seed 123456  2>&1")

