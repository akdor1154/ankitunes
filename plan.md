__version__ = '0.1.0'

# run custom practice session?

# on each next,
# - pull next card from sched - FocusTune
# - pull 2-3 random other cards matching type - OtherTunes
# - shuffle set OR always do next card as final.
# - display
# Card 1
# [show]
# Card2
# [show]
# Card3
# [show]

# [Next]

# Options -
# hooks:
# card_will_show -> grab new cards here, save in q
# web:_showQuestion needs to be changed to show multiple qs
# _showAnswer needs to say (subclass _showEaseButtons or _showAnswerButtons, or stuff with gui_hooks.reviewer_did_show_answer)
#  "How was [FocusTune]?"


# Aims -
Phase 0 -
<!-- Subclass Reviewer, get it to show, prove it by
print('hi from custom')
and -->
adding a hook.