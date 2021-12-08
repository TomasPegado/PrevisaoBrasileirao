# Código para obter as chances de um time de vencer o Brasileirão

* O programa retorna as chances dos times na Série A do campeonato em um dicionário(dict_previsao)

## Modelo

* O modelo probabilístico utilizado foi de um artigo publicado por um grupo de matemáticos da UFMG

* [Link para o artigo](https://silo.tips/download/probabilidades-no-futebol)

## Importação dos dados

* Os dados utilizados foram importados do site [API Futebol](https://www.api-futebol.com.br/)

    - Para usar esse código de modo eficiente é preciso fazer login nesse site e 
    gerar sua chave para as requisições dos dados. Essa chave é usada para puxar os dados
    por meio da api do site.
    
    - Podem usar o código com a minha chave, mas pode ocorrer de ter atingido o limite de requisições
    do site ou a chave não estar atualizada.
    
    - Conferir se seu plano no site permite puxar dados das rodadas do campeonato.

    - Conferir o limite de requisições permitidas por dia pelo site para o plano gratuito.
