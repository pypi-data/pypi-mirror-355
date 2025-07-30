from balinese_embeddingvector.pretrained.BaliWord2Vec import BaliWord2Vec


pretrained_model = BaliWord2Vec(
    huggingface_repo_ID='satriabimantara/balinese_pretrained_wordembedding').load_pretrained_model()
print(pretrained_model.wv['Satua'])
print(pretrained_model.wv.most_similar('Lutung'))
