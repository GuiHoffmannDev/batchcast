# Experimento 2: a premissa do modelo vertical não se sustenta nesta escala de dado

Continuação do spike. Testa a premissa central da empresa: **ajustar em bioprocesso melhora a
previsão num processo novo?** Data: 2026-11-13. Apple M5, CPU apenas.

Modelo: Chronos-2, Apache-2.0, 119.477.664 parâmetros, com trainer no próprio pacote
`chronos-forecasting`. O TimesFM 3.0 ficou fora porque a licença proíbe ajuste fino para uso
comercial e proíbe usar resultados em decisão comercial.

## Resumo: resultado negativo, e ele é caro de ignorar

| Braço | MASE | Perda quantílica | Cobertura marginal |
|---|---|---|---|
| **Chronos-2 zero-shot** | linha de base | linha de base | **0,792** |
| Teto, ajustado na própria levedura | +3,6% (vence 58%) | +9,5% (vence 62%) | 0,670 |
| Melhor transferência, 18 corridas de CHO | +2,0% (53%) | +1,8% (53%) | 0,794 |
| Transferência com treino 6x mais forte | **−8,7% (42%)** | −7,0% (43%) | 0,648 |
| Controle, tempo embaralhado | −2,8% (44%) | −1,3% (47%) | 0,724 |
| Conformal multiplicativo | +0,0% | −0,0% | 0,793 |

Quatro conclusões, nenhuma favorável ao plano original.

1. **Transferir de outro organismo não entrega nada.** De +0,5% a +2,0%, com taxa de vitória de
   51% a 53%, que é cara ou coroa. A curva de escala de dado não sobe.
2. **Treinar mais piora.** O braço com 6 épocas e taxa de aprendizado 5 vezes maior ajustou o
   doador muito melhor, perda de 6,52 para 3,28, e degradou a levedura em 8,7%. Esquecimento
   catastrófico. Isso descarta subtreino como explicação do resultado nulo.
3. **O teto em distribuição é baixo, e o que ele compra é nitidez, não calibração.** Ajustar na
   própria levedura rende +9,5% de perda quantílica, mas derruba a cobertura marginal de 0,792
   para 0,670. Fica mais afiado e menos confiável.
4. **O Chronos-2 zero-shot já está calibrado.** Cobertura marginal 0,792 contra nominal de 0,80,
   erro de 0,008. A predição conformal confirmou isso de forma independente: ela encontrou fator
   de escala em torno de 1,0 e não mudou nada, porque não havia nada para corrigir.

A lacuna que eu pensei existir, de calibração, **não existe**. E a lacuna de acurácia não se fecha
com dado de bioprocesso nesta escala.

## Correção de método: eu errei a definição de calibração

Isto inverte uma manchete do primeiro documento e precisa ficar registrado.

A coluna `coverage` dos meus CSVs é a fração dos 64 passos do horizonte que caem dentro da faixa,
calculada por janela e por canal. **Calibração se mede pela média disso sobre as janelas**, que é
a cobertura marginal. Eu reportei a **mediana**.

A distribuição é bimodal: 28,5% das janelas têm cobertura de 100% e 17,5% têm abaixo de 50%. Com
essa forma, média e mediana divergem muito.

| Braço | Marginal, correto | Mediana, o que eu reportei | Erro marginal |
|---|---|---|---|
| Chronos-2 zero-shot multivariado | **0,792** | 0,953 | **−0,008** |
| Transferência CHO N=12 | 0,799 | 0,953 | −0,001 |
| Conformal multiplicativo | 0,793 | 0,953 | −0,007 |
| Teto em distribuição | 0,670 | 0,797 | −0,130 |
| TimesFM 3.0 só com setpoints | 0,663 | 0,797 | −0,137 |

Estreitar a faixa puxa a mediana para baixo, em direção a 0,80, **e empurra a marginal para fora
de 0,80**. Pela mediana parece melhora, pela marginal é piora. Afirmações do primeiro documento
que isto invalida:

- que o ajuste fino cortava o erro de calibração 6,4 vezes. Falso, ele piora a calibração.
- que os braços com covariável de setpoint eram os melhores calibrados. Falso, marginal 0,663 e
  0,671 contra 0,792 do zero-shot.
- que todos os modelos de fundação ficavam largos demais. Falso para o Chronos-2 multivariado.

É o segundo erro de agregação neste projeto, depois do de comparar medianas em vez de pares.
Mesma causa nos dois: **agregar antes de comparar**. A regra que passou a valer é comparar
emparelhado e usar a média quando a métrica é uma taxa.

## Desenho

| Item | Valor |
|---|---|
| Doador | `uhlendorff2026_cho`, 24 corridas de CHO-K1, DOI `10.5281/zenodo.20829178`, CC BY 4.0 |
| Alvo | `uhlendorff2026`, 52 corridas de levedura, DOI `10.5281/zenodo.19690248`, CC BY 4.0 |
| Canais | os 5 que os dois conjuntos compartilham, na mesma ordem |
| Amostragem | 0,25 h exatos nos dois, zero valor faltante |
| Linha de base | Chronos-2 zero-shot multivariado, mesmo caminho de chamada |
| Avaliação | as mesmas 780 janelas canônicas de todo o spike |
| Treino padrão | contexto 192, horizonte 64, passo 32, lote 4, AdamW, lr 1e-5, 2 épocas |

Os dois conjuntos vêm do mesmo grupo e usam a mesma instrumentação, o que torna o teste limpo:
**mesmos sensores, biologia radicalmente diferente.**

| | Levedura | CHO-K1 |
|---|---|---|
| Temperatura | 21,7 a 22,7 °C | 36,6 a 37,2 °C |
| pH | 3,6 a 6,0 | 7,0 a 7,1 |
| Duração | 77 h | até 328 h |
| Pontos utilizáveis | 77.035 | 100.135 |

Disciplina, verificada por asserção que falha a execução:

- Levedura **nunca** entra no treino do braço de transferência.
- O braço em distribuição divide por **campanha**, nunca por corrida, porque os 4 reatores de uma
  campanha são réplicas. As 3 dobras cobrem as 52 corridas exatamente uma vez.
- Entrada em `float32` confirmada idêntica bit a bit à `float64` da linha de base.

## A curva de escala não sobe

| Corridas de CHO | Pontos de treino | Passos | Perda | MASE | Vence |
|---|---|---|---|---|---|
| 6 | 23.930 | 52 | 6,66 para 6,03 | +0,5% | 52% |
| 12 | 48.570 | 106 | 5,93 para 5,03 | +1,7% | 53% |
| 18 | 75.775 | 170 | 5,88 para 5,60 | +2,0% | 53% |
| 24 | 100.135 | 224 | 6,34 para 5,14 | +0,7% | 51% |
| 24, treino forte | 100.135 | 672 | 6,52 para **3,28** | **−8,7%** | 42% |
| 24, embaralhado | 100.135 | 224 | 8,61 para 8,64 | −2,8% | 44% |

A curva vai 0,5, 1,7, 2,0, 0,7. Sobe e volta, sem tendência. E o braço de treino forte, que
ajustou o doador melhor que todos, é o pior na levedura. **Mais dado não ajuda e mais treino
prejudica.**

### O controle negativo validou o pipeline

Com o tempo embaralhado dentro de cada canal, o que preserva a distribuição marginal e destrói a
dinâmica, a perda **não caiu**: 8,6062 para 8,6433 em 224 passos. Tarefa inaprendível, como
deveria ser. O modelo resultante ficou pior que o zero-shot.

Isso exclui a explicação alternativa de que o meu laço de treino fabricaria ganho espúrio por
simples adaptação a escala ou taxa de amostragem.

### O único canal que transferiu foi o errado

Melhor braço de transferência, N=18:

| Canal | MASE | Vence |
|---|---|---|
| temperatura | **+10,9%** | 72% |
| permissividade (biomassa) | +0,4% | 51% |
| pH | +0,3% | 51% |
| oxigênio dissolvido | −1,9% | 47% |
| CO2 dissolvido | −2,1% | 47% |

O modelo aprendeu que temperatura é um setpoint quase constante e bem controlado. Isso é fato de
engenharia de controle e transfere de CHO para levedura porque ambos são reatores controlados,
não porque ambos são biologia. Os canais que carregam a biologia, permissividade para biomassa,
CO2 para atividade metabólica e oxigênio para respiração, não ganharam nada ou pioraram.

## O teto em distribuição: nitidez à custa de calibração

Ajustado na própria levedura, 3 dobras por campanha, 52 corridas cobertas uma vez cada, com
apenas 64 a 73 janelas de treino e 32 a 36 passos por dobra.

| Métrica | Zero-shot | Teto em distribuição |
|---|---|---|
| MASE | linha de base | +3,6% (vence 58%) |
| Perda quantílica | linha de base | **+9,5% (vence 62%)** |
| Cobertura marginal | **0,792** | 0,670 |

O ganho de perda quantílica é quase três vezes o de MASE, e vem de intervalos mais estreitos. Mas
a cobertura marginal cai 0,122 abaixo do nominal. Em decisão operacional isso é uma troca ruim:
o intervalo fica mais bonito e mente mais. Um intervalo de 80% que cobre 67% subestima o risco
em um terço dos casos.

Ganho por contexto, estável:

| Contexto | MASE | Perda quantílica |
|---|---|---|
| 32 (8 h) | +4,1% (59%) | +10,6% (64%) |
| 64 (16 h) | +3,4% (57%) | +7,6% (59%) |
| 96 (24 h) | +3,3% (57%) | +9,3% (61%) |
| 128 (32 h) | +3,8% (57%) | +10,0% (63%) |
| 192 (48 h) | +3,7% (56%) | +9,3% (62%) |

## A predição conformal confirmou que não há o que calibrar

Duas tentativas, ambas com as mesmas dobras por campanha e calibração só no conjunto de
calibração.

**CQR aditivo**, no estilo Romano, Patterson e Candès 2019. Falhou e eu entendi por quê: o
deslocamento é aditivo e a suposta má calibração seria multiplicativa. Além disso minha
reinterpolação linear dos quantis internos destruiu a mediana e piorou o MASE de 4,62 para 5,32.
Erro meu de implementação, registrado.

**Conformal multiplicativo**, escalando a faixa em torno da mediana do modelo, que preserva o
MASE por construção. Fatores de escala encontrados: de 0,70 a 1,64, concentrados em torno de 1,0.
Resultado: cobertura marginal 0,793 contra 0,792 do zero-shot. **Nenhuma mudança.**

Esse é o achado, não a falha: um procedimento de calibração que busca o fator necessário e
encontra 1,0 está dizendo que a faixa já estava certa.

## O que isso faz com a estratégia

| Item | Plano anterior | Corrigido pela medição |
|---|---|---|
| Premissa | pré-treinar em bioprocesso bate o modelo geral | não bate nesta escala; treinar mais piora |
| Lacuna de calibração | existe e é a oportunidade | **não existe**; o zero-shot já acerta |
| Moat | corpus proprietário | não há moat de modelo a esta escala |
| O que sobra | — | camada de aplicação, integração e estar dentro da planta |

O que **continua válido** do primeiro experimento e não foi tocado por este: o Chronos-2 zero-shot
bate os métodos triviais de 13% a 33% no canal de biomassa, em todo tamanho de contexto. Existe
valor real em aplicar modelo de fundação de série temporal a bioprocesso.

O que este experimento mata é a ideia de **construir o seu próprio**. A 10⁵ pontos, o modelo
vertical não aparece. A pergunta de negócio muda de "como treino o modelo" para "o que eu
construo em volta de um modelo Apache-2.0 que já funciona".

## Limitações, e uma delas é grande

- **Escala de dado minúscula.** 100.135 pontos no doador, contra mais de 1 trilhão no pré-treino
  do TimesFM-3. A curva plana num intervalo de 4 vezes, nessa escala absoluta, **não** permite
  extrapolar para 10⁹ pontos. O resultado diz que a transferência não funciona com 10⁵ pontos.
  **Não diz que nunca funcionaria.** Esta é a limitação que mais limita a conclusão.
- **Um par de organismos, num sentido só.** CHO para levedura. Não diz nada sobre transferência
  entre fermentações próximas, por exemplo levedura cervejeira para levedura de cana, que é
  justamente o caso da cunha e provavelmente o caso favorável. Esse é o teste que faltou.
- **Ajuste fino completo, sem LoRA e sem congelar camadas.** Com 10⁵ pontos e 119M parâmetros,
  ajuste completo é a receita do esquecimento catastrófico, e foi o que se observou. LoRA ou
  congelar o tronco provavelmente degradariam menos, e não foram testados.
- **Uma semente por braço, dois protocolos de treino.** Sem busca de hiperparâmetro e sem parada
  antecipada em conjunto de validação do doador.
- **O teto em distribuição não é um teto verdadeiro.** É o que 32 a 37 corridas entregam. Com mais
  corridas do mesmo processo sobe, e não medi quanto.

## Como reproduzir

```bash
VIRTUAL_ENV=.venv uv pip install chronos-forecasting

# inventario e harmonizacao de canais entre organismos
.venv/bin/python -I spike/data_bioprocess.py  data/atlas/release

# curva de escala: ajusta em CHO, avalia em levedura
.venv/bin/python -I spike/run_transfer.py  data/atlas/release \
    --out results/yeast_transfer.csv --donor-sizes 6,12,18,24 --epochs 2

# controle negativo: tempo embaralhado dentro de cada canal
.venv/bin/python -I spike/run_transfer.py  data/atlas/release \
    --out results/yeast_transfer_shuf.csv --donor-sizes 24 --epochs 2 --control

# descarta subtreino: 6 epocas, lr 5e-5
.venv/bin/python -I spike/run_transfer.py  data/atlas/release \
    --out results/yeast_transfer_hard.csv --donor-sizes 24 --epochs 6 --lr 5e-5 --suffix _hard

# teto em distribuicao: ajusta na propria levedura, dobras por campanha
.venv/bin/python -I spike/run_indist.py  data/atlas/release \
    --out results/yeast_indist.csv --folds 3 --epochs 2

# conformal, sem treinar: aditivo (falhou) e multiplicativo (o correto)
.venv/bin/python -I spike/run_conformal.py   data/atlas/release --out results/yeast_conformal.csv
.venv/bin/python -I spike/run_conformal2.py  data/atlas/release --out results/yeast_conformal2.csv

# tabelas de decisao e verificacao
.venv/bin/python -I spike/analyze_transfer_test.py  results
.venv/bin/python -I spike/verify.py        # 46 checagens; sai 1 se alguma falhar
```

### Arquivos novos

| Caminho | Conteúdo |
|---|---|
| `spike/data_bioprocess.py` | carrega qualquer conjunto do Atlas nos 5 canais compartilhados |
| `spike/run_transfer.py` | curva de escala, controle embaralhado, teto de passos |
| `spike/run_indist.py` | teto em distribuição com dobras por campanha |
| `spike/run_conformal.py` | CQR aditivo; falhou, mantido como registro do erro |
| `spike/run_conformal2.py` | conformal multiplicativo preservando a mediana |
| `spike/analyze_transfer_test.py` | tabelas de transferência, escala, controle e teto |
| `spike/verify.py` | 46 checagens cobrindo os dois experimentos |

### Verificações que precisam passar

1. **Levedura nunca no treino de transferência**, por asserção de interseção vazia.
2. **Divisão por campanha**, não por corrida, no teto em distribuição; as 3 dobras cobrem as 52
   corridas exatamente uma vez.
3. **`float32` idêntico a `float64`** na entrada, verificado bit a bit, para a comparação com a
   linha de base não ter artefato de tipo.
4. **Controle negativo não aprende**: a perda tem que ficar plana com o tempo embaralhado.
   Observado 8,6062 para 8,6433.
5. **Limiar de conformal calibrado só no conjunto de calibração.**
6. **Calibração medida pela cobertura marginal**, a média, nunca pela mediana.
7. **Os 46 números citados nos dois documentos** conferidos contra os CSVs por `verify.py`.
