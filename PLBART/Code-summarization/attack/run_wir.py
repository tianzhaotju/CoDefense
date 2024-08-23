import os

os.system("python attack_wir.py \
    --output_dir=../saved_models \
    --model_name_or_path ../../../Model/PLBART/checkpoint_11_100000.pt \
    --load_model_path ../saved_models/checkpoint-best-bleu/pytorch_model.bin \
    --tokenizer_name=../../../Model/PLBART/sentencepiece.bpe.model \
    --csv_store_path ../result/plbart_sum_wir.csv \
    --dev_filename=../../../Data/Code-summarization/test_sampled.jsonl \
    --eval_batch_size 128 \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --seed 123456")

