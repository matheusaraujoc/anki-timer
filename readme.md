# Study Timer Dock para Anki

> Um cronômetro de estudos discreto e integrado nativamente na interface do Anki.

O Study Timer Dock foi projetado para estudantes que utilizam técnicas de produtividade (como Pomodoro ou Timeboxing) e desejam manter o foco sem alternar janelas. Ele reside na lateral da janela de revisão como um painel nativo.

---

<p align="center">
  <img src="./screenshots/preview.png" alt="Preview do Addon" width="600">
</p>
<p align="center">
  <em>Visualização do Timer no Anki com diferentes modos de aparência</em>
</p>

---

## Funcionalidades Principais

* **Integração Nativa:** Funciona como uma barra lateral (Dock) fixa. Pode ser fechada, aberta ou movida sem cobrir os cartões.
* **Design Responsivo:**
    * **Modo Circular:** Visualização gráfica do progresso.
    * **Modo Foco:** Interface minimalista numérica.
    * **Dark Mode Automático:** Ajusta as cores instantaneamente conforme o tema do Anki.
* **Configurações Persistentes:** O addon salva suas preferências automaticamente (tempo, modo de visualização, configurações de som).
* **Foco:**
    * Botão de configurações discreto (aparece apenas ao passar o mouse).
    * Interface limpa.
* **Produtividade:**
    * **Alerta Sonoro:** Opção de aviso sonoro ao finalizar.
    * **Loop Automático:** Opção para reiniciar o ciclo automaticamente.

## Instalação

### Via AnkiWeb
1. Abra o Anki e vá em **Ferramentas** > **Complementos**.
2. Clique em **Obter Complementos**.
3. Insira o código: `(CÓDIGO_DO_ANKIWEB_AQUI)` e clique em OK.
4. Reinicie o Anki.

### Instalação Manual (GitHub)
1. Baixe a versão mais recente na aba Releases ou clone este repositório.
2. Copie a pasta `study_timer_dock` para o diretório de addons do Anki:
    * **Windows:** `%APPDATA%\Anki2\addons21`
    * **Mac:** `~/Library/Application Support/Anki2/addons21`
    * **Linux:** `~/.local/share/Anki2/addons21`
3. Reinicie o Anki.

## Guia de Uso

### 1. Ativando o Timer
Vá no menu superior: **Ferramentas** -> **Abrir Sidebar de Estudo**.

### 2. Controles
* Defina os **Minutos** e **Segundos** na parte inferior.
* Clique em **INICIAR** para começar a contagem.
* O botão mudará para **PAUSAR** e **RETOMAR** conforme necessário.
* **PARAR** reseta o tempo para o total inicial.

### 3. Ajustes
Passe o mouse sobre o canto superior direito do painel do timer. O ícone de configurações (⛭) aparecerá. Clique para configurar:

* **Aparência:** Alterne entre o visual Gráfico ou Texto.
* **Reiniciar auto:** O timer recomeça automaticamente ao chegar em zero.
* **Alerta sonoro:** Toca um aviso do sistema ao fim do tempo.

## Tecnologias

Desenvolvido em **Python 3** utilizando **PyQt6** (via `aqt`).
* Renderização vetorial com `QPainter`.
* Hooks do sistema para reatividade de temas.
* Gerenciamento de configuração via JSON.

## Contribuição

Pull requests são bem-vindos. Para mudanças maiores, por favor abra uma issue primeiro para discutir o que você gostaria de mudar.

## Licença

Distribuído sob a licença MIT. Veja o arquivo LICENSE para mais informações.