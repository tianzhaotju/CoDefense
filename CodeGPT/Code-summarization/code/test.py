import os
os.system("python run.py \
    --output_dir=../saved_models_codegpt_sum_style/ \
    --model_type=gpt2 \
    --tokenizer_name=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --model_name_or_path=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --load_model_path=../saved_models_codegpt_sum_style/checkpoint-best-bleu/pytorch_model.bin \
    --do_test \
    --train_filename=../../../adv_data/Code-summarization/CodeGPT/style/adv_train.jsonl \
    --dev_filename=../../../adv_data/Code-summarization/CodeGPT/style/valid.jsonl \
    --test_filename=../../../adv_data/Code-summarization/CodeGPT/style/adv_test_2.jsonl \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 32 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    --seed 123456 2>&1")

