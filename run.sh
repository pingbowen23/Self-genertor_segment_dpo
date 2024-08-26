numbers=(2000 1500 1500)
len_min=(0 10000 20000)
len_max=(10000 20000 32000)
for i in {0..0}
do
    python Back_trans.py --number ${numbers[$i]} \
    --context_len_min ${len_min[$i]} \
    --context_len_max ${len_max[$i]}
done