# Farke PDF Generator

I like to play this game a lot and I like to have nicely made PDFs to keep score with. 

So I vibe coded this quick little Python script to generate the perfect score sheet for your perfect little game. 

I like to use virtual envs to keep everything clean and portable.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Then you can run the script like such as below:

```bash
usage: farkle.py [-h] [-r ROUNDS] [-p PLAYERS] [-o OUTPUT]
farkle.py: error: argument -p/--players: Players must be between 1 and 8.
farkle.py: error: argument -r/--rounds: Rounds must be between 1 and 20.
```
