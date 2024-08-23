import os

os.system("python run.py \
    --output_dir=../saved_models_plbart_sum_style/ \
    --model_type=bart \
    --model_name_or_path=../../../Model/PLBART/checkpoint_11_100000.pt \
    --tokenizer_name=../../../Model/PLBART/sentencepiece.bpe.model \
    --do_train \
    --do_eval \
    --train_filename=../../../adv_data/Code-summarization/PLBART/style/adv_train.jsonl \
    --dev_filename=../../../adv_data/Code-summarization/PLBART/style/valid.jsonl \
    --test_filename=../../../adv_data/Code-summarization/PLBART/style/adv_test_2.jsonl \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 16 \
    --eval_batch_size 16 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    2>&1")

