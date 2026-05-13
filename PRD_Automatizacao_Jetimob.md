---
# PRD – Automação de Edição de Imóveis Jetimob

## 1. Objetivo do Projeto
Automatizar, com alta resiliência e robustez, o processo de edição de imóveis cadastrados na plataforma Jetimob, utilizando Python e Selenium, garantindo:
- Execução persistente e reiniciável;
- Diagnóstico preciso de falhas e propriedades “não encontradas”;
- Fácil distribuição via executável (.exe);
- Monitoramento e relatórios detalhados executando sem intervenção manual, mesmo diante de variáveis de ambiente e UI do Jetimob.

## 2. Usuários e Stakeholders
- Usuário Final: Operador do setor imobiliário ou T.I. responsável por atualizar registros no Jetimob.
- Time de T.I./Manutenção: Futuros programadores, analistas, ou sistemas de I.A. necessários para manutenção, correção ou melhoria.
- Gerência: Pode receber relatórios sobre progresso, erros e estimativas.

## 3. Fluxo Geral da Automação
### 3.1. Preparação
- O usuário posiciona o arquivo imoveis.json na pasta de trabalho (mesmo local do .exe).
- Automatização é iniciada via duplo clique no executável.

### 3.2. Execução Principal
1. Login: Faz login na plataforma Jetimob com credenciais fornecidas.
2. Iteração: Para cada imóvel do arquivo imoveis.json, executa:
   - Pesquisa o imóvel pelo código.
   - Navega até a tela de edição.
   - Realiza as alterações/correções necessárias.
   - Salva alterações.
   - Atualiza checkpoint se o processo foi concluído.
3. Tratativa de exceções:
   - Se imóvel não encontrado, salva código em imoveis_nao_encontrados.txt.
   - Em caso de falhas recuperáveis (modais, overlays, ou travamentos de navegação), tenta interações alternativas e registra no log.
   - Em falhas não recuperáveis, registra erro em jetimob_erros.json, avança para o próximo imóvel e segue processamento.
4. Saída:
   - Ao concluir o lote ou ser interrompido, gera relatório detalhado (relatorio_execucao.txt).
   - No próximo start, retoma automaticamente do ponto de parada (“checkpoint”) e ignora imóveis já processados ou não encontrados.

## 4. Estrutura de Arquivos
- jetimob_automation.py: Script principal com lógica da automação e definição das funções.
- config.py: Definições de constantes de ambiente, paths e configurações editáveis.
- imoveis.json: Fonte de dados contendo uma lista de códigos dos imóveis (formato: lista de strings ou objetos JSON).
- jetimob_progresso.json: Armazena o estado do processamento, última posição processada, etc.
- jetimob_erros.json: Erros detalhados com timestamp/código, mensagem e contexto.
- imoveis_nao_encontrados.txt: Lista de códigos de imóveis não localizados (um por linha, sem repetições).
- relatorio_execucao.txt: Sumário da execução (total processado, erros, ignorados, tempo médio por imóvel, ETA, imóveis não encontrados).
- dist/jetimob_automacao.exe: Executável distribuível.
- teste_jetimob_runner.py: Script auxiliar para testes e debug.
- Auxiliares: logs temporários, versões de backup, etc.

## 5. Requisitos Funcionais
### 5.1 Persistência e Resiliência
- Salvar progresso após cada imóvel editado para garantir retomada estável e sem repetições/loops.
- Reconhecimento e manipulação de elementos dinâmicos, overlays e modais bloqueantes.
- Tolerância a lentidão, timeouts e pequenas instabilidades do Jetimob (retries, waits inteligentes).
- Identificação automática de campos obrigatórios, bloqueados ou invisíveis.

### 5.2 Relatórios e Diagnóstico
- Gerar relatório final de execução, tornando explícito:
  - Imóveis processados com sucesso
  - Imóveis não encontrados
  - Falhas/imóveis com erro
  - Statísticas gerais (tempo, média, ETA)
- Logs detalhados para uso em debug e auditoria.

### 5.3 Interface de Operação
- Compatibilidade total com Windows para distribuição como .exe (via PyInstaller).
- Operações de caminho/arquivo sempre relativas ao diretório do executável.
- Rodar em modo headless e interativo.
- NÃO requer interação manual durante execução (totalmente automatizado).

## 6. Especificação das Funções Principais
### 6.1 login(driver, usuario, senha)
Realiza o login automático no Jetimob, navegando para a tela inicial após autenticação.
- Recebe driver Selenium, usuário e senha.
- Implementa lógica de retry em caso de falha momentânea.

### 6.2 load_imoveis(path)
Carrega o arquivo de imóveis e retorna a lista de códigos a ser processada.

### 6.3 checkpoint_handler(action: “save” | “load”, dados)
Salva ou carrega o progresso da automação (jetimob_progresso.json).
- Permite garantir reinício robusto.

### 6.4 editar_imovel(driver, codigo)
Executa o fluxo completo de edição deste imóvel:
- Pesquisa pelo código, navega para tela de edição, faz mudanças, salva e trata modais.
- Utiliza técnicas de bypass para overlays, inputs bloqueados ou campos não clicáveis.

### 6.5 registrar_nao_encontrado(codigo)
Adiciona o código em imoveis_nao_encontrados.txt, evitando duplicatas.

### 6.6 registrar_erro(codigo, detalhes)
Salva no jetimob_erros.json o código, motivo do erro, status, timestamp.

### 6.7 gerar_relatorio()
Gera e salva relatorio_execucao.txt com todos dados consolidados.

### 6.8 utils.py
Funções de suporte para:
- Execução de waits customizados;
- Clicks alternativos (via JS ou scroll);
- Manipulação e supressão de elementos de UI que bloqueiam o fluxo automatizado;
- Geração de timestamp legível, log formatado, etc.

## 7. Boas Práticas e Notas Técnicas
- Código modular e documentado com docstrings em todas as funções.
- Captura de exceções com mensagens informativas e registros nos arquivos corretos.
- Tempo de execução, posição atual, e estatísticas de progresso sempre atualizados.
- Sempre limpar/atualizar checkpoint após cada imóvel.
- Foco em legibilidade, manutenção e robustez frente a mudanças visuais do Jetimob.
- Ao rodar via .exe, todos arquivos auxiliares devem ser criados e lidos no diretório do executável (use os.path.dirname(sys.argv[0]) ).
- Não há exposição de dados sensíveis nos arquivos de log ou relatório.
- Funções devem ser facilmente editáveis e testáveis de modo isolado.

## 8. Possíveis Extensões Futuras
- Internacionalização/idioma do relatório.
- Parametrização por linha de comando (ex: arquivos de entrada, período de espera).
- Interface gráfica para status em tempo real.
- Integração com sistemas de notificação (push, email).
- Execução paralela em lote.

## 9. Glossário
- Driver: instância Selenium WebDriver usada para manipular o navegador.
- Overlay/Modal: camadas visuais que impedem interação com elementos da página.
- Checkpoint: Estado salvo do processamento, permitindo retomar após interrupção.
- ETA: Estimativa do tempo de conclusão do lote.

## 10. Disclaimer & Manutenção
Ao alterar este projeto:
- Respeite a estrutura de arquivos e chaves citadas acima.
- Garanta a persistência e robustez dos checkpoints.
- Atualize docstrings, comentários e o log de mudanças.

# Resumo Visual dos Arquivos e Funções

dist/
  jetimob_automacao.exe          ← Executável principal
jetimob_automation.py           ← Script e funções principais
config.py                       ← Configurações gerais
imoveis.json                    ← Entrada de códigos de imóveis
jetimob_progresso.json          ← Checkpoint (progresso atual)
jetimob_erros.json              ← Falhas detalhadas
imoveis_nao_encontrados.txt     ← Imóveis não localizados
relatorio_execucao.txt          ← Relatório final
teste_jetimob_runner.py         ← Runner de teste/desenvolvimento
utils.py                        ← Funções auxiliares (espera, clique, scroll, logs, etc)

Se desejar, este PRD pode ser salvo junto ao repositório para referência e onboarding futuro! Se quiser que eu adicione exemplos de docstring, snippet de cabeçalho ou template de função, é só pedir.