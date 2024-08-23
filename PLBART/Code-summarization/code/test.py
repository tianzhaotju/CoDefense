import os

os.system("python run.py \
    --do_test \
    --load_model_path ../saved_models_plbart_sum_style/checkpoint-best-bleu/pytorch_model.bin \
    --model_type=bart \
    --model_name_or_path=../../../Model/PLBART/checkpoint_11_100000.pt \
    --tokenizer_name=../../../Model/PLBART/sentencepiece.bpe.model \
    --train_filename=../../../adv_data/Code-summarization/PLBART/style/adv_train.jsonl \
    --dev_filename=../../../adv_data/Code-summarization/PLBART/style/valid.jsonl \
    --test_filename=../../../adv_data/Code-summarization/PLBART/style/adv_test_2.jsonl \
    --output_dir ../saved_models_plbart_sum_style/ \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 32 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    --seed 123456  2>&1")
