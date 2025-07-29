# ScreenGrab 

## Functionality

<!-- For accessability if it stops working: 
export PATH="$HOME/Personal_Projects/ScreenGrab:$PATH" 
source ~/.bashrc
-->

When installing via pip, in order for the AI to work you must do the following:
run:
- export OPENAI_API_KEY=""

to check it is set: 
- echo $OPENAI_API_KEY

To persist across sessions: 
`echo 'export OPENAI_API_KEY=""' >> ~/.bashrc
source ~/.bashrc` or zsh instead of bash

In your terminal, enter the command: windowgpt --p <"accompanied prompt with the ss"> --s <"save">





