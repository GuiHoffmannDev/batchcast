# Spike: modelos de fundação de séries temporais em bioprocesso

Decisão interna de seguir ou parar. Trabalho descartável, dado público, sem parceiro.
Data: 2026-11-12. Hardware: Apple M5, 16 GB, CPU apenas.

## Resumo executivo

52 corridas reais de fermentação de levedura, 780 janelas de previsão, quatro modelos de
fundação, quatro linhas de base triviais e uma linha de base de PCA, todos nas mesmas janelas
verificadas por asserção. Rodou inteiro em CPU num Mac.

### Veredito: seguir, com o produto e a aposta arquitetural trocados

**Existe sinal.** Com 48 h de histórico, os modelos de fundação batem as linhas triviais entre
14% e 29%, emparelhado janela a janela. Isso não era garantido e é o resultado que mantém a tese
viva.

**Mas quatro coisas que o plano assumia estão erradas.**

#### 1. A licença do TimesFM 3.0 proíbe usar estes números para decidir a empresa

O texto define uso não comercial como aquele em que "os resultados não são usados em tomada de
decisão comercial". É exatamente o uso deste spike. A cláusula também veda treinar ou destilar
outro modelo com fim comercial a partir dele.

A boa notícia é que a rota limpa não custa desempenho. TimesFM 2.5 e Chronos-2 são Apache-2.0, e
são iguais ou melhores.

#### 2. Escolher o modelo não é vantagem. Chegar rápido é.

Com 48 h de histórico, os quatro modelos empatam entre si: taxa de vitória emparelhada de 48% a
49%, ou seja, cara ou coroa. Mesmo teto.

A diferença está no histórico curto, e é grande:

| Contexto | Chronos-2 bate o trivial | TimesFM 3.0 bate o trivial |
|---|---|---|
| 8 h | **+28,6%** | perde |
| 16 h | +22,7% | perde |
| 32 h | +27,6% | perde |
| 48 h | +24,3% | +19% |

O Chronos-2 funciona com 8 h de uma batelada de 72 h. O TimesFM 3.0 precisa de 48 h, ou seja, só
serve no último terço. Para aviso precoce, que é o uso que vale dinheiro, essa é a única
diferença que importa. E o Chronos-2 faz isso com 119 milhões de parâmetros contra 330 milhões.

#### 3. Nenhuma escolha arquitetural passa de 10%. A vantagem é o modelo contra o trivial.

O plano apostava que a atenção entre sensores seria decisiva, porque a causa de um desvio mora em
outro canal. Testado, nada no espaço arquitetural é grande:

| Variação | Ganho emparelhado |
|---|---|
| Multivariado conjunto, Chronos-2, biomassa, 48 h de histórico | +10,0% |
| Covariáveis de setpoint, TimesFM 3.0 | +3,6% |
| Covariáveis de setpoint, Chronos-2 | +3,2% |
| Multivariado conjunto, TimesFM 3.0 | −0,7% |

O que é grande é a comparação com o método trivial. No canal de biomassa, Chronos-2 multivariado
contra repetir o último valor, de +13% a +33% conforme o contexto, vencendo de 57% a 76% das
janelas.

Mas há uma ressalva que puxa para o outro lado: **as covariáveis de setpoint consertam a
calibração**. Os dois braços que as usam ficam em 0,797 e 0,812 contra o nominal de 0,80,
enquanto todos os outros erram de −0,10 a +0,14. Para decisão operacional isso vale mais que os
3% de acurácia, porque é o que permite usar a incerteza em vez de só a linha central.

Uma correção de método que devo registrar: numa primeira leitura reportei 12% de ganho para as
covariáveis, por comparar medianas de braços que cobriam janelas diferentes. Emparelhado, são
3,6%. Duas asserções de verificação pegaram esse erro e um segundo, de rótulo duplicado, e a
seção de método no Resultado 2 explica a regra que passei a usar.

A implicação prática inverte a aposta: não há atalho de arquitetura. A lacuna explorável é que
**nenhum destes modelos viu bioprocesso no pré-treino**, mais a calibração ruim. Ambas se fecham
com dado, não com engenhosidade de atenção.

#### 4. O produto mais vendável não precisa de modelo de fundação

Detecção de desvio era a aposta: usar a faixa de quantis como alarme grátis. Testado em desenho
pareado, com 4 corridas a 37 °C contra 4 controles idênticos a 22 °C na mesma campanha, e com a
temperatura removida da entrada:

| Método | Falso positivo | Detecção | 1º alarme |
|---|---|---|---|
| **PCA com 2 componentes** | **6,7%** | **100%** | **4,75 h** |
| Chronos-2, faixa de quantis | 16,7% | 0% | — |
| TimesFM 3.0, faixa de quantis | 16,7% | 25% | 44 h |

O motivo é estrutural, não de ajuste: **um previsor condicionado no histórico anômalo trata a
anomalia como o novo normal.** Ele prevê a batelada quente corretamente, a observação cai dentro
da faixa, nenhum alarme dispara. Quanto melhor o previsor, menos ele alarma. O PCA ganha porque
tem o que falta ao previsor, um modelo de referência do que é normal.

### Decisão

**Seguir para a fase de dado proprietário, com três correções de rota.**

| Item | Plano original | Corrigido pela medição |
|---|---|---|
| Produto | alarme de desvio | previsão de trajetória e ponto final |
| Linha de base a bater | especialistas publicados por processo | Chronos-2, Apache-2.0, 119M, grátis |
| Aposta arquitetural | atenção entre sensores | nenhuma; o ganho vem de pré-treino em bateladas e de calibração |
| Modelo de referência | TimesFM 3.0 | Chronos-2 ou TimesFM 2.5, por licença |

A barra é mais alta do que o plano supunha: um modelo geral, gratuito e pequeno já bate o trivial
em 24% com 8 h de histórico. Mas as lacunas que sobram são concretas e endereçáveis, e nenhuma
depende de ter mais computação que o Google:

1. **Nenhum destes modelos viu bioprocesso no pré-treino.** O corpus do TimesFM-3 tem mais de
   um trilhão de pontos e a composição por domínio não foi publicada, mas as bancadas em que
   esses modelos competem, GIFT-Eval, FEV-Bench e TIME, não contêm biologia. Um corpus de
   bateladas é a única lacuna que exige dado proprietário, e é por isso que ela é defensável.
2. **Desempenho com histórico curto**, que é onde o dinheiro está e onde só um dos quatro modelos
   funciona hoje.
3. **Calibração dos quantis**, hoje larga demais em todos os modelos, e que é o que impede usar
   a incerteza para decidir. Foi parte da causa da falha na detecção de desvio.

## O que foi medido

Tarefa: dado o histórico dos canais inline de uma batelada, prever as próximas 16 h de todos os
canais, com os 9 quantis de 0,1 a 0,9.

| Item | Valor |
|---|---|
| Conjunto | `uhlendorff2026` do Bioprocess Atlas, DOI `10.5281/zenodo.19690248`, CC BY 4.0 |
| Corridas | 52, reais, propagação de levedura cervejeira |
| Organismos | *Saccharomyces cerevisiae* (26) e *S. pastorianus* (26) |
| Canais densos | temperatura, pH, oxigênio dissolvido, CO2 dissolvido, permissividade |
| Grade temporal | 0,25 h exatos, 291 pontos medianos, 72,8 h de duração |
| Horizonte | 64 pontos, 16 h |
| Contextos | 32, 64, 96, 128, 192 pontos, ou 8 h a 48 h |
| Origens por corrida | 3, igualmente espaçadas |
| Métricas | MASE e perda quantílica ponderada por canal, convenção GIFT-Eval, mais cobertura |

A grade é limpa: 0 corridas com mais de 2% de valor faltante após interpolação, e os 5 canais
densos compartilham o mesmo eixo de tempo. 5 das 52 corridas têm buracos de até 5,75 h, que
entram na interpolação e estão reportados.

## Resultado 1: TimesFM 3.0 não bate o trivial

Mediana sobre corrida, origem, contexto e canal. 3.899 janelas por braço.

| Braço | MASE | WQL | Cobertura |
|---|---|---|---|
| `E_last_value` repetir último valor | **6,018** | 4,741 | 0,547 |
| `B_tfm3_univar` TimesFM 3.0 canal a canal | 6,201 | — | 0,781 |
| `A_tfm3_multivar` TimesFM 3.0 multivariado | 7,106 | — | 0,734 |
| `E_linear_extrap` extrapolação linear | 8,521 | 7,145 | 0,648 |
| `E_drift` deriva | 10,729 | 9,251 | 0,328 |
| `E_seasonal_naive` naive sazonal | 11,544 | 8,826 | 0,234 |

Ganho do melhor modelo de fundação sobre a melhor linha trivial: **−3,0%**. Negativo.

Taxa de vitória por janela, que é livre de escala e confirma o MASE:

| Braço | % de janelas em que vence |
|---|---|
| `E_last_value` | 32,0 |
| `B_tfm3_univar` | 17,6 |
| `A_tfm3_multivar` | 16,9 |
| `E_linear_extrap` | 16,0 |
| `E_drift` | 14,1 |
| `E_seasonal_naive` | 3,6 |

Repetir o último valor vence em quase um terço das janelas, mais que qualquer outro método.

Duas ressalvas que o Resultado 2 desenvolve, e sem as quais esta tabela engana:

- **O agregado mistura contextos.** O TimesFM 3.0 perde do trivial com 8 h a 32 h de histórico e
  ganha com 48 h. O −3,0% é a média dessas duas situações opostas, não um resultado uniforme.
- **Esta tabela não contém o Chronos-2 nem o TimesFM 2.5**, que se comportam de forma diferente.
  O título vale para o TimesFM 3.0 e só para ele.

### A atenção entre variáveis depende do canal e do contexto

Comparação emparelhada, mesmos pesos, mesmas janelas. Valor positivo significa que prever os
canais em conjunto foi melhor que prever um a um.

Por canal, agregado sobre contextos:

| Canal | TimesFM 3.0 | Chronos-2 |
|---|---|---|
| permissividade (biomassa) | −0,1% | +2,6% |
| pH | **−10,0%** | +2,3% |
| CO2 dissolvido | −0,6% | +2,2% |
| oxigênio dissolvido | +0,2% | +1,2% |
| temperatura | −0,2% | **−4,4%** |

O agregado esconde o efeito. No Chronos-2, por contexto, na permissividade:

| Contexto | Ganho do multivariado |
|---|---|
| 32 (8 h) | **−9,5%** |
| 64 (16 h) | +1,4% |
| 96 (24 h) | +6,2% |
| 128 (32 h) | +3,6% |
| 192 (48 h) | **+10,0%** |

Três leituras, todas com mecanismo plausível:

**A correlação entre canais precisa de histórico para ser estimada.** Com 8 h o multivariado
atrapalha, com 48 h ele rende +10%. Faz sentido: estimar como os canais se informam exige ver os
canais se moverem juntos por tempo suficiente.

**A temperatura é a exceção consistente, e deveria ser.** Perde em todos os contextos, de −1,2% a
−7,8%. É um canal controlado de fora, com setpoint, então os canais biológicos só adicionam ruído
para prevê-lo. O modelo não sabe disso e tenta usá-los.

**No TimesFM 3.0 a atenção entre variáveis não funciona.** Nada em quatro canais e −10% no pH,
onde vence só 31% das janelas. Isso é notável, porque essa pilha é a novidade anunciada da
versão 3.0 e o motivo declarado de escolhê-la para biorreator.

Então a premissa de que a causa de um desvio mora em outro canal **se sustenta, mas só no
Chronos-2, só nos canais biológicos e só com histórico suficiente**. Magnitude de 2% a 10%, não
de 20%.

O multivariado é também muito mais barato por canal, porque emite todos num passe só: 5 ms no
Chronos-2 contra 5 ms no univariado, e 18 ms contra 61 ms no TimesFM 3.0.

Nota de método: a razão entre as medianas dos dois braços do TimesFM dá −14,6%, muito pior que o
emparelhamento. A diferença vem das caudas. Os números emparelhados acima são os corretos.

## Resultado 2: o que separa os modelos é a rapidez, não o teto

Quatro modelos nas mesmas 780 janelas, verificadas idênticas por asserção.

| Modelo | Parâmetros | Licença dos pesos |
|---|---|---|
| TimesFM 3.0 | 330.710.976 | TimesFM Non-Commercial v1.0 |
| TimesFM 2.5 | 200 M | Apache-2.0 |
| Chronos-2 | 119.477.664 | Apache-2.0 |

### Com histórico longo, todos empatam e todos batem o trivial

Comparação emparelhada no contexto de 192 pontos, ou 48 h, 780 janelas, 5 canais:

| Braço | MASE mediano |
|---|---|
| `C_chronos2_multivar` | 2,842 |
| `Bp_tfm25_univar` | 3,135 |
| `C_chronos2_univar` | 3,377 |
| `B_tfm3_univar` | 3,612 |
| `A_tfm3_multivar` | 4,404 |
| `E_last_value` | 4,461 |
| `E_linear_extrap` | 4,586 |

A ordem das medianas sugere diferenças entre modelos. O emparelhamento mostra que não há:

| TimesFM 2.5 contra | Ganho mediano | Vence em |
|---|---|---|
| Chronos-2 multivariado | −1,4% | 48% |
| Chronos-2 univariado | −1,2% | 48% |
| TimesFM 3.0 univariado | −0,4% | 49% |
| Repetir último valor | **+14,6%** | **66%** |
| Extrapolação linear | **+28,6%** | **67%** |

**Com 48 h de histórico os quatro modelos de fundação são estatisticamente indistinguíveis entre
si, e todos batem as linhas triviais entre 14% e 29%.** Taxa de vitória de 48% a 49% é empate.

Isso é, por si, uma notícia boa para a tese: existe sinal que os métodos triviais não capturam.
E é notícia ruim para a ideia de ganhar por escolher o modelo certo, porque o teto é o mesmo.

### Com histórico curto, só o Chronos-2 funciona

Aqui mora a diferença que importa para o produto. MASE mediano por tamanho de contexto, 5 canais:

| Contexto | TimesFM 3.0 univar | Chronos-2 univar | Último valor | Chronos vs TimesFM 3.0 |
|---|---|---|---|---|
| 32 (8 h) | 9,069 | 6,349 | 8,886 | **+30,0%** |
| 64 (16 h) | 9,322 | 5,358 | 6,930 | **+42,5%** |
| 96 (24 h) | 6,774 | 4,568 | 6,023 | **+32,6%** |
| 128 (32 h) | 5,055 | 3,885 | 5,368 | +23,1% |
| 192 (48 h) | 3,612 | 3,377 | 4,461 | +6,5% |

E contra o trivial, que é o teste que decide se há sinal:

| Contexto | Chronos-2 bate o trivial em |
|---|---|
| 32 (8 h) | **+28,6%** |
| 64 (16 h) | +22,7% |
| 96 (24 h) | +24,2% |
| 128 (32 h) | +27,6% |
| 192 (48 h) | +24,3% |

**O Chronos-2 bate o trivial de 22,7% a 28,6% em todo tamanho de contexto, inclusive com 8 h.**
O TimesFM 3.0 só empata com o trivial até 32 h e só vence com 48 h.

Numa batelada de 72 h isso é a diferença entre avisar no começo e fazer autópsia. A vantagem do
Chronos-2 não é um teto mais alto, é **chegar ao teto com um sexto do histórico**.

Agregado sobre todos os contextos, o que mistura as duas situações:

| Confronto | Ganho mediano | Vence em |
|---|---|---|
| Chronos-2 univar contra TimesFM 3.0 univar | +11,4% | 63% |
| Chronos-2 univar contra repetir último valor | +12,7% | 62% |
| TimesFM 3.0 univar contra repetir último valor | +0,0% | 50% |

O +0,0% do TimesFM 3.0 contra o trivial é a média de perder no curto e ganhar no longo.

### Covariáveis de setpoint: pouco no ponto, muito na incerteza

Alvo único `permittivity_pF_cm`, que é o proxy de biomassa, com temperatura e pH como covariáveis
passado-futuro. É o cenário realista: numa planta esses dois são setpoints de receita e são
genuinamente conhecidos para todo o horizonte.

Comparado sempre contra o univariado **da mesma família e da mesma configuração**, no conjunto
natural de pares de cada confronto:

| Confronto | Ganho mediano | Vence em | n |
|---|---|---|---|
| TimesFM 3.0: só setpoints contra univariado | +3,6% | 56% | 468 |
| Chronos-2: covariáveis contra univariado | +3,2% | 54% | 780 |
| TimesFM 3.0: covariáveis contra univariado | +2,7% | 55% | 468 |
| Chronos-2: covariáveis contra multivariado | **+0,0%** | **50%** | 780 |

**No ponto previsto, a covariável rende de 3% a 4%, e empata exatamente com prever os canais em
conjunto.** Taxas de vitória de 50% a 56% são quase cara ou coroa.

Dois detalhes que importam:

**Covariável só-passado não acrescenta nada, e talvez atrapalhe.** O braço que recebe apenas
temperatura e pH como passado-futuro rende +3,6%, e o braço que recebe também oxigênio e CO2 como
só-passado rende +2,7%. Canais cujo futuro é desconhecido não ajudam. O valor vem inteiramente de
saber o futuro da receita.

**Na incerteza, a covariável é a única coisa que funciona.** Cobertura da faixa de 0,1 a 0,9,
cujo nominal é 0,80, no conjunto natural de cada braço:

| Braço | Cobertura | Desvio do nominal |
|---|---|---|
| `A2b_tfm3_setpoints_only` | **0,797** | **−0,003** |
| `A2_tfm3_covariates` | **0,812** | **+0,012** |
| `C_chronos2_covariates` | 0,844 | +0,044 |
| `C_chronos2_univar` | 0,891 | +0,091 |
| `C_chronos2_multivar` | 0,938 | +0,138 |
| `B_tfm3_univar_sym` | 0,703 | −0,097 |
| `A_tfm3_multivar_sym` | 0,719 | −0,081 |

Os dois braços com covariável de setpoint acertam a calibração praticamente de fábrica. Todos os
outros erram para um lado ou para o outro, e os do Chronos-2 erram para largo, o que significa
dizer "não sei" quando sabe.

Informar ao modelo o futuro da receita, portanto, **compra pouca acurácia e muita confiabilidade
de intervalo**. Para decisão operacional isso vale mais do que os 3% sugerem, porque é o que
permite usar a incerteza para decidir em vez de só olhar a linha central.

### Nota de método sobre comparações emparelhadas

Dois números do meu primeiro rascunho estavam errados e vale registrar por quê, porque o erro é
fácil de repetir.

Comparar a mediana do braço A com a mediana do braço B **só vale se os dois cobrirem exatamente
as mesmas janelas**. Comparei medianas de braços com coberturas diferentes e a covariável
pareceu render 12%. Emparelhado, rende 2,7%.

Na correção, errei para o outro lado: usei a interseção de **todos** os braços, que tem só 156
janelas e exclui os contextos em que alguns braços não rodaram. Isso distorceu tanto o ponto
quanto a calibração, e me fez descartar o efeito de calibração que é real.

A regra correta, usada nas tabelas acima: **para cada confronto, o conjunto natural de pares
daqueles dois braços**, com o n reportado ao lado.

### O efeito grande é sempre o mesmo: modelo contra trivial

Nenhuma variação arquitetural passou de 10%. O que passa, e com folga, é a comparação com os
métodos triviais. Na permissividade, Chronos-2 multivariado contra repetir o último valor:

| Contexto | Ganho | Vence em |
|---|---|---|
| 32 (8 h) | +14,7% | 67% |
| 64 (16 h) | +13,1% | 57% |
| 96 (24 h) | +17,7% | 66% |
| 128 (32 h) | +22,4% | 67% |
| 192 (48 h) | **+33,3%** | **76%** |
| todos | +19,9% | 67% |

**Esta é a tabela mais importante do spike.** No canal de interesse comercial, o Chronos-2 bate o
método trivial em todo tamanho de contexto, de +13% a +33%, vencendo de 57% a 76% das janelas.
É o resultado que sustenta a tese, e ele não depende de nenhuma escolha arquitetural fina.

## Resultado 3: detecção de desvio, e aqui o modelo de fundação perde feio

Esta é a tarefa mais ligada a dinheiro: avisar que a batelada está desviando. Era também a que
parecia sair de graça, usando a faixa de quantis como sinal de anomalia sem treinar detector.

**Não sai de graça. Não funciona.**

### Desenho, sem vazamento de rótulo

As campanhas EXP007 e EXP008 dão um controle pareado quase perfeito. Nelas, os reatores R01 e R02
rodaram a 22 °C e R03 e R04 a 37 °C, com cepa, pré-cultura, densidade de mosto, aeração e volume
idênticos. A única variável é a temperatura.

| Grupo | n | Composição |
|---|---|---|
| Positivos | 4 | 37 °C, duas cepas, 3 h de pré-cultura, 12 °P |
| Controles pareados | 4 | 22 °C, mesmas campanhas, todo o resto igual |
| Negativos amplos | 30 | 22 °C, 12 °P, demais condições |

A temperatura foi **removida da entrada** dos modelos. A detecção tem que vir do efeito
biológico em pH, oxigênio dissolvido, CO2 dissolvido e permissividade. O limiar de alarme foi
calibrado **só nos negativos**, nunca nos positivos.

### Resultado

| Método | Percentil | Falso positivo amplo | Falso positivo pareado | Detecção | 1º alarme |
|---|---|---|---|---|---|
| **PCA SPE, k=2** | 99,5 | **6,7%** | **0%** | **100%** | **4,75 h** |
| PCA SPE, k=3 | 99,0 | 20,0% | 0% | 100% | 7,75 h |
| PCA SPE, k=1 | 99,0 | 13,3% | 25% | 50% | 4,25 h |
| Chronos-2, faixa de quantis | 97,5 | 30,0% | 25% | 25% | 48,0 h |
| Chronos-2, faixa de quantis | 99,0 | 16,7% | 25% | **0%** | — |
| TimesFM 3.0, faixa de quantis | 99,0 | 16,7% | 25% | 25% | 44,0 h |

A separação bruta mostra que o sinal está lá e é forte:

| Grupo | SPE mediano por corrida |
|---|---|
| Negativos a 22 °C | 0,469, faixa de 0,079 a 1,639 |
| Controles pareados a 22 °C | 0,412, faixa de 0,172 a 1,280 |
| Positivos a 37 °C | **2,010**, faixa de 1,148 a 3,411 |

**PCA com 2 componentes, método dos anos 1960, detecta 100% das bateladas estressadas com 6,7%
de falso positivo amplo, 0% nos controles pareados, e avisa em 4,75 h de uma batelada de 72 h.**
Os dois modelos de fundação, usados como detector por faixa de quantis, detectam no máximo 25% e
só avisam em 44 h a 48 h, quando o processo já acabou de fato.

Para referência de ordem de grandeza, a linha de base de PCA publicada no IndPenSim reporta
16,4% de falso positivo com 100% de detecção e 1,60 h de atraso. Processo e falha são diferentes,
então não é comparação direta, mas o PCA aqui está na mesma vizinhança de qualidade.

### Por que falha, e o que isso significa

O mecanismo é estrutural, não um defeito de ajuste.

Um previsor condicionado no próprio histórico anômalo **trata a anomalia como o novo normal**.
Dadas 16 h de uma batelada que roda quente, o modelo prevê corretamente a continuação quente, a
observação cai dentro da faixa, e nenhum alarme dispara. Quanto melhor o previsor, menos ele
alarma.

O PCA funciona porque tem outra coisa: um **modelo de referência do normal**, construído a partir
de corridas normais. Ele não pergunta "a série continua como vinha", pergunta "esta correlação
entre canais é compatível com o que já vi em batelada boa".

Consequências diretas para o produto:

1. **A faixa de quantis não é um detector de anomalia para mudança de regime persistente.** Pode
   servir para pico súbito ou falha de sensor, que não entram no contexto. Não serve para
   batelada que nasce errada ou deriva devagar, que são os casos que custam dinheiro.
2. **O alarme de desvio, que é o produto mais vendável, não precisa de modelo de fundação.** Já
   é resolvido por um método trivial a 6,7% de falso positivo.
3. **O que sobra para o modelo de fundação é previsão, não alarme.** Dizer para onde a batelada
   vai, que é soft sensing e previsão de ponto final. Nisso o Chronos-2 ganha do trivial entre
   13% e 25%.

Isso estreita o produto e deve estrear qualquer conversa com parceiro industrial. Vender "modelo
de fundação detecta desvio" seria vender algo que o PCA faz melhor.

## Resultado 4: transferência entre cepa, escala e campanha

Avaliado no contexto de 192, o único em que o zero-shot vence.

**Cepa.** W-34/70, que é *S. pastorianus* de baixa fermentação, é mais difícil que W-68 para
todos os métodos. A razão entre cepas do TimesFM univariado é 0,58, praticamente igual à de
repetir o último valor, 0,60, e muito melhor que a da extrapolação linear, 0,34. O modelo de
fundação não transfere melhor entre cepas que o trivial, mas também não transfere pior.

**Escala.** As 4 corridas em 10 L são mais fáceis que as 48 em 0,7 L para todo método, com
melhora de 31% a 59%. Isso **não** demonstra que a transferência de escala funciona: demonstra
que aquele subconjunto é mais suave. Com 4 corridas não há como separar as duas coisas. Este
teste ficou inconclusivo e precisa de mais corridas em escala grande.

**Campanha.** Aqui está o achado útil. A amplitude do MASE entre as 13 campanhas:

| Braço | Mediana | Melhor campanha | Pior campanha | Amplitude |
|---|---|---|---|---|
| `B_tfm3_univar` | 2,955 | 1,016 | 7,341 | **6,325** |
| `E_linear_extrap` | 3,790 | 1,699 | 15,049 | 13,350 |
| `A_tfm3_multivar` | 3,983 | 1,041 | 8,837 | 7,796 |
| `E_last_value` | 4,196 | 1,733 | 7,737 | 6,004 |

Nenhum método é estável: todos variam por fator de 4 a 7 entre lotes. Mas o TimesFM univariado
tem a melhor mediana e a segunda menor amplitude. **A vantagem do modelo de fundação aqui é
consistência entre lotes, não acurácia mediana.** Isso é vendável de outra forma e muda o
discurso.

## Calibração

Cobertura empírica da faixa 0,1 a 0,9, cujo valor nominal é 0,80. **Depende fortemente do
tamanho do contexto**, e reportar só a média engana.

Agregado sobre todos os contextos:

| Braço | Cobertura | Leitura |
|---|---|---|
| `B_tfm3_univar` | 0,781 | calibrado |
| `A_tfm3_multivar` | 0,734 | levemente estreito |
| `C_chronos2_univar` | 0,891 | largo |
| `C_chronos2_multivar` | 0,938 | largo |

Só no contexto de 192, onde os modelos são precisos:

| Braço | Cobertura |
|---|---|
| `E_last_value` | 0,797 |
| `E_linear_extrap` | 0,766 |
| `C_chronos2_univar` | 0,922 |
| `C_chronos2_multivar` | 0,953 |
| `B_tfm3_univar` | 0,969 |
| `A_tfm3_multivar` | 0,969 |
| `Bp_tfm25_univar` | 0,984 |

**Todos os modelos de fundação ficam largos demais com histórico longo.** O TimesFM 2.5 chega a
0,984 contra o nominal de 0,80: a faixa de 80% cobre 98% das observações, ou seja, é quase três
vezes mais larga do que deveria.

A exceção são os braços com covariável de setpoint, que acertam quase de fábrica: 0,797 no
`A2b_tfm3_setpoints_only` e 0,812 no `A2_tfm3_covariates`, contra 0,80 nominal, cada um no seu
conjunto natural de 468 janelas. Informar o futuro da receita melhora pouco o ponto e muito o
intervalo.

Por que isso importa: faixa larga demais significa que o modelo diz não saber quando na verdade
sabe. Para decisão operacional, um intervalo três vezes mais largo que o real é inutilizável, e
foi parte do motivo da falha na detecção de desvio. Recalibrar quantis em dado de bioprocesso é
barato e é uma das lacunas concretas que um modelo vertical fecharia.

## Varredura de configuração

Feita antes de fixar o braço, para que a escolha não seja garimpo de resultado. 6 corridas,
contexto 192, as 8 combinações de `use_znorm`, `padding_mode` e `use_symmetric_averaging`.

| Achado | Efeito |
|---|---|
| `use_znorm` ligado ou desligado | **zero**, números idênticos |
| `padding_mode` `none` ou `edge` | **zero** com contexto suficiente |
| `use_symmetric_averaging` ligado | MASE 4,661 contra 4,813, WQL 3,686 contra 4,035 |

Configuração não resgata o modelo. O ganho do averaging simétrico é de 3%, muito menor que a
lacuna até a linha trivial.

## Licenças, com texto verificado

Baixado de `huggingface.co/google/timesfm-3.0-pytorch/raw/main/LICENSE` em 2026-11-12 e salvo em
`docs/timesfm-3.0-LICENSE.txt`.

| Modelo | Parâmetros | Licença dos pesos | Uso comercial |
|---|---|---|---|
| `google/timesfm-3.0-pytorch` | 330.710.976 | TimesFM Non-Commercial v1.0 | **não** |
| `google/timesfm-2.5-200m-pytorch` | 200 M | Apache-2.0 | sim |
| `amazon/chronos-2` | 119.477.664 | Apache-2.0 | sim |

A cláusula que decide:

> "Non-Commercial Purpose" means use for testing, evaluation, or research not tied to commercial
> gain, production deployment, or revenue generation. This includes internal benchmarking,
> academic research, and experimentation on private or public datasets, **provided the results
> are not used in commercial decision-making**, client deliverables, or paid products/services.

E a cláusula que fecha a rota de destilação:

> use (c) to train, fine-tune, or distill other models for commercial use ... is not a
> Non-Commercial Purpose.

Não sou advogado e isto precisa de confirmação profissional. Mas a leitura direta é que os
números do TimesFM 3.0 neste documento servem para entender o domínio e **não** para fundamentar
a decisão de negócio. Os números do Chronos-2 e do TimesFM 2.5 servem, porque Apache-2.0 não tem
restrição de campo de uso.

## Limitações deste spike

Ditas antes de qualquer conclusão ser usada.

- **Uma repetição por janela, sem sementes múltiplas nem intervalo de confiança.** Escolha
  deliberada de escopo para decisão interna, registrada no plano.
- **Estimativa pontual não é idêntica entre modelos.** Para o TimesFM usei `forecast`, para o
  Chronos usei a média retornada. O ranking do WQL, que não depende dessa escolha, concorda com o
  ranking do MASE, o que defende a conclusão.
- **MASE é alto em termos absolutos**, de 3 a 12, porque o denominador é a diferença de um passo
  numa série suave amostrada a 15 min. Serve para ordenar métodos, não para ler como erro
  relativo.
- **O IndPenSim não foi obtido e deixou de ser necessário.** O arquivo de 503,8 MB no Zenodo
  (DOI `10.5281/zenodo.21786646`) serviu a 215 KB/s e caiu para 5 KB/s, reiniciando do zero três
  vezes apesar de `curl --retry 8 -C -`. O download foi abortado por decisão de escopo, não por
  falta de tentativa. Deixou de bloquear porque o IndPenSim é simulação, e o próprio plano dizia
  que ele serve para medir lacuna relativa entre arquiteturas e nunca como prova para um cliente.
  A detecção de desvio foi medida em dado real, com desenho controlado, na seção própria. As
  linhas de base de PCA publicadas no IndPenSim seguem citadas apenas como ordem de grandeza.
- **Transferência de escala inconclusiva**, com 4 corridas em 10 L.
- **Um único conjunto de dados, um único organismo.** Levedura cervejeira não é fermentação de
  etanol de cana, embora seja o organismo mais próximo com dado aberto.
- **O TimesFM 2.5 rodou só no contexto de 192 e sem `torch.compile`.** A compilação na CPU ficou
  mais de 20 min sem sair do lugar e foi desligada. Logo a comparação do 2.5 nos contextos curtos
  não existe, e o número de latência dele não é comparável aos outros.
- **A configuração do TimesFM 2.5 não é idêntica à do 3.0.** Usei `use_continuous_quantile_head`
  e `fix_quantile_crossing`, que não têm equivalente no braço do 3.0. A comparação de ponto vale,
  a de calibração entre esses dois é frouxa.
- **4 positivos na detecção de desvio.** O desenho é limpo e pareado, mas 4 é pouco. O intervalo
  de confiança de uma taxa de detecção com n=4 é enorme. O que o resultado sustenta é a direção e
  o mecanismo, não o valor exato de 100% ou 0%.
- **Um só tipo de desvio.** Estresse térmico sustentado desde o início. Nada diz sobre falha de
  sensor, contaminação ou deriva lenta, que têm assinaturas diferentes e nos quais a faixa de
  quantis pode se comportar melhor.

## Como reproduzir

Ambiente, do zero:

```bash
uv venv --python 3.12 .venv
VIRTUAL_ENV=.venv uv pip install "timesfm[torch,mlx]==3.0.2" chronos-forecasting \
    pandas numpy scikit-learn scipy pyarrow
```

Dado, cada conjunto em diretório próprio e vazio:

```bash
git clone --depth 1 https://github.com/anupama29k/Bioprocess-Atlas.git data/atlas
```

Execução, em ordem. Os scripts ficam em `spike/` e recebem o caminho do dado como argumento,
nunca o contrário, e rodam com `python -I` porque o dado baixado é material não confiável.

```bash
.venv/bin/python -I spike/inspect_atlas.py  data/atlas/release
.venv/bin/python -I spike/inspect_grid.py   data/atlas/release uhlendorff2026
.venv/bin/python -I spike/data_yeast.py     data/atlas/release
.venv/bin/python -I spike/probe_config.py   data/atlas/release

.venv/bin/python -I spike/run_eval.py       data/atlas/release --out results/yeast_sweep.csv
.venv/bin/python -I spike/run_chronos.py    data/atlas/release --out results/yeast_chronos.csv
.venv/bin/python -I spike/run_tfm25.py      data/atlas/release --out results/yeast_tfm25.csv
.venv/bin/python -I spike/run_covariates.py data/atlas/release results/yeast_cov_tfm3.csv
.venv/bin/python -I spike/run_fault_yeast.py data/atlas/release

.venv/bin/python -I spike/analyze.py          results/yeast_sweep.csv
.venv/bin/python -I spike/analyze_transfer.py results/yeast_sweep.csv data/atlas/release
.venv/bin/python -I spike/analyze_all.py      results
.venv/bin/python -I spike/fix_pca.py          data/atlas/release

.venv/bin/python -I spike/verify.py           # 28 checagens; sai 1 se alguma falhar
```

`spike/verify.py` confere **todo número citado neste documento** contra os CSVs, usando para cada
confronto o conjunto natural de pares daqueles dois braços. Rodou 28 de 28. Se um número for
editado aqui sem a medição correspondente, a verificação falha.

### Verificações que precisam passar

As três primeiras são asserções no código e falham a execução se quebrarem.

1. **Janelas idênticas entre arquivos de resultado.** Os 780 trios de corrida, origem e contexto
   são iguais nos arquivos do TimesFM e do Chronos. Sem isso nenhuma comparação vale.
2. **Metadados presentes para toda corrida** em `analyze_transfer.py`.
3. **Desenho pareado intacto** em `run_fault_yeast.py`: exatamente 4 positivos a 37 °C e
   4 controles pareados nas mesmas campanhas.
4. **Limiar de alarme calibrado só em negativos.** Nenhuma corrida positiva entra na escolha do
   limiar.
5. **Zero-shot não treina**, logo não há vazamento possível de treino para teste nos braços de
   modelo. As linhas de base triviais também não ajustam nada entre janelas.
6. **Quantis monotônicos** nas linhas de base, verificado no teste de fumaça.
7. **Cobertura empírica** comparada ao nominal de 0,80 em toda tabela de resultado.

### Arquivos

| Caminho | Conteúdo |
|---|---|
| `spike/data_yeast.py` | carrega as 52 corridas como matrizes `(canais, tempo)` na grade de 0,25 h |
| `spike/metrics.py` | MASE, perda quantílica ponderada, cobertura |
| `spike/baselines.py` | último valor, deriva, extrapolação linear, naive sazonal |
| `spike/run_eval.py` | braços do TimesFM 3.0 e triviais, define as janelas canônicas |
| `spike/run_chronos.py` | braços do Chronos-2, reusa as janelas de `run_eval` |
| `spike/run_tfm25.py` | braço do TimesFM 2.5, o Apache-2.0 |
| `spike/run_covariates.py` | braços com covariáveis passado-futuro |
| `spike/run_fault_yeast.py` | detecção de desvio com desenho pareado e linha de base PCA |
| `spike/analyze*.py` | tabelas de decisão, transferência e comparação entre modelos |
| `spike/fix_pca.py` | linha de base PCA com k < número de canais |
| `spike/verify.py` | confere os 28 números citados neste documento |
| `results/*.csv` | uma linha por braço, corrida, origem, contexto e canal |
| `docs/timesfm-3.0-LICENSE.txt` | licença baixada e verificada em 2026-11-12 |
