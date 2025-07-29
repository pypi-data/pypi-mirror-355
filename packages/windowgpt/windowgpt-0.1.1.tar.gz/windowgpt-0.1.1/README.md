# windowgpt

<!-- For accessability if it stops working: 
export PATH="$HOME/Personal_Projects/ScreenGrab:$PATH" 
source ~/.bashrc
-->

## Install:
`pip install windowgpt`


## How to use:

Obtain an API key from [Open AI](https://platform.openai.com/docs/overview).

In Terminal export this API key using the following command: `export OPEN_API_KEY="<your_key>"`

When you close your terminal, it won't remember your key. To make sure it remembers your key run this command:

`echo 'export OPENAI_API_KEY=""' >> ~/.bashrc`

`source ~/.bashrc`

Now if this doesn't work, you will have to supply the key to windowgpt using the --key flag.

## Example

windowgpt --p <"prompt"> --s <"save"> --key <"API_KEY">

--p is a compulsory flag.

--s only include if you want to save the screenshot.

--key use when providing an API key.




