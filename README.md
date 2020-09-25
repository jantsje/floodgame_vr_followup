# floodgame_vr_followup
This application uses the control treatment of the floodgame. It was developed for use in the VR lab and has a question about presence and simulator sickness. The experiment starts with a screen where the experimenter is asked to give the subject ID. The experiment only includes survey questions that are part of the preregistration. This means that the following variables have been deleted (compared to `floodgame_online`): responsible, neighbors, independence, collectivism, numeracy, concern, probability_exact and beliefs.

To install the app to your local oTree directory, copy the folder 'floodgame_vr_followup' to your oTree Django project and extend the session configurations in your ```settings.py``` at the root of the oTree directory:

```
SESSION_CONFIGS = [
    dict(
        name='floodgame_vr_followup',
        display_name="Floodgame for VR",
        num_demo_participants=1,
        app_sequence=['floodgame_vr_followup'],
        demo=False,
        language='nl'
    )
                  ]
```

## Languages
* English 
* Dutch (through Django localization file)

Note that the understanding questions rely on [otree-utils](https://github.com/WZBSocialScienceCenter/otreeutils). 

## Issues
Localization was not stable for the *UnderstandingQuestionsPage*, which is why the questions have been translated manually. This issue should be solved if one wants to conduct an experiment simultaneously in two countries. 
