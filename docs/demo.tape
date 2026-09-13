# vhs docs/demo.tape  -> docs/img/demo.gif
Output "docs/img/frames/"
Set Shell bash
Set FontSize 15
Set Width 1000
Set Height 560
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set Padding 18
Hide
Type "source .venv/bin/activate && export PS1='$ ' PYTHONWARNINGS=ignore && clear"
Enter
Show
Type "cat examples/playwright/test_search_results.py | tail -11"
Sleep 300ms
Enter
Sleep 3.5s
Type "pytest examples/playwright -q"
Sleep 300ms
Enter
Sleep 6s
Sleep 2s
