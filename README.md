# AMR Parser

[DyNet](https://github.com/clab/dynet) implementation of the transition-based AMR parser. We provide the code for aligner and the parser. You can find all the details in the following paper:

- [ Better Transition-Based AMR Parsing with a Refined Search Space](http://www.statnlp.org/research/sp/zhijiang18emnlp.pdf). (Zhijiang Guo and Wei Lu. EMNLP 2018)

## Requirements

In order to train the parser, you will need to have the following installed:

- Python 3.5.2
- [DyNet 2.0](https://github.com/clab/dynet)
- [JAMR](https://github.com/jflanigan/jamr)
- [MGIZA++](https://github.com/moses-smt/mgiza)

Notice that we do not support DyNet version higher than 2.0.

## Usage 

### Hybrid Aligner
Get the AMR corpus (LDC2014T12/LDC2015E86/LDC2017T10). We can't distribute them because them paid. Put the folder called abstract_meaning_representation_amr_2.0 (for LDC2017T10) inside the data folder. Then we rename the folder as amr. Before we run the proprocess script. We should specify four directories: **REPO_DIR** and **DATA_DIR**. **REPO_DIR** refers to the directory of the current repository. **DATA_DIR** refers to the amr directory. For example, DATA_DIR=${REPO_DIR}/data/amr. 

For LDC2015E86 and LDC2017T10 corpus, named entities in AMR are now marked up with their :wiki values. We remove them before feed the AMR graphs into the aligner. During the postprocessing stage, we pick the most frequent wikification for that entity (‘-’, if unseen) according to a look-up table in the training set.

- For LDC2014T12 corpus, run the bash script:
```
./preprocess.sh
```

- For LDC2015E86 or LDC2017T10 corpus, run the bash script:
```
./preprocess_rmwiki.sh
```

Aftering running the script, you can find preprocessed AMR files under the amr/tmp_amr folder, which contains train, dev and test three folders. Then put the amr.txt files under these three folders to JAMR aligner by running:
```
. scripts/config.sh
scripts/ALIGN.sh < amr.txt > train.2014
```

We need to get the aligned files for train, dev and test amr files. Then we put three aligned files into one folder called jamr_ouput inside the data folder. Before runing the hybrid aligner, we also need to specify two directories: **REPO_DIR** and **JAMR_FILE**. **JAMR_FILE** refers to the output of the JAMR aligner. Here is train.2014. Then we run the bash script to get the transition sequences for training the AMR parser:

```
./align.sh
```

Finally, we get four new files: train.transtions, dev.transitions, test.transitions and train.txt.pb.lemmas. train.txt.pb.lemmas is the look-up table for predicate and lemma concept (look at the paper for more details.)

We also leave some AMR samples in the folders mentioned above to show the usage.

### AMR Parser
Now we are ready for train our own AMR parser.
#### Train a new AMR parser
```
./train.py --dynet-mem 6600 --train_file data/train.transitions --lemma_practs data/train.pb.lemmas --dev_file data/dev.transitions --gold_AMR_dev data/amr/tmp_amr/dev/amr.txt --emb_file data/sskip.100.vectors
```

Link to the word vectors that we used in the ACL 2015 paper for English: [sskip.100.vectors](https://drive.google.com/file/d/0B8nESzOdPhLsdWF2S1Ayb1RkTXc/view?usp=sharing). The training process should be stopped when the development SMATCH score does not substantially improve anymore (around epoch 16).

#### Parsing with a trained parser
```
./train.py --dynet-mem 6600 --load_model 1 --train_file data/train.transitions --lemma_practs data/train.pb.lemmas --dev_file data/test.transitions --gold_AMR_dev data/amr/tmp_amr/test/amr.txt --emb_file data/sskip.100.vectors
```

### Citation

If you make use of this software, please cite the following:

    @InProceedings{D18-1198,
    author = "Guo, Zhijiang and Lu, Wei",
    title = "Better Transition-Based AMR Parsing with a Refined Search Space",
    booktitle = "Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing",
    year = "2018"
    }
