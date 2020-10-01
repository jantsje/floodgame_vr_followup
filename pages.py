from . import models
from ._builtin import Page, WaitPage
from .models import Constants
from floodgame_vr_followup.extra_pages import Check as UnderstandingQuestionsPage
import locale
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.utils import translation
from django.conf import settings


class TransMixin:
    def get_context_data(self, **context):
        user_language = self.session.config.get('language', 'en')
        translation.activate(user_language)
        if hasattr(settings, 'LANGUAGE_SESSION_KEY'):
            self.request.session[settings.LANGUAGE_SESSION_KEY] = user_language
        return super().get_context_data(**context)
        print(user_language)


class Page(TransMixin, Page):
    pass


class WaitPage(TransMixin, WaitPage):
    pass


def vars_for_all_templates(self):
    player = self.player
    participant = self.participant
    return_vars = {'progress': progress(self),
                   'cumulative_payoff': participant.vars["cumulative_payoff"],
                   'risk': player.risk, 'round': player.round_number,
                   'scenario_nr': player.scenario_nr,
                   'insurance_choice': participant.vars["insurance_choice"],
                   'language_code': self.session.config['language']
                   }
    return_vars.update(self.player.vars_for_scenarios())
    return return_vars


def progress(p):
    progress_rel = p.round_number/Constants.num_rounds*100
    return str(locale.atof(str(progress_rel)))
    # this looks really bad but it has to do with the NL language settings in Django
    # and the fact that the progressbar does not work with comma separators for decimals


class Spelpagina(Page):
    def get_form_fields(self):
        return self.form_fields + ['opened']


class Welcome(Page):
    form_model = 'player'

    def vars_for_template(self):
        return {'participation_fee': self.session.config['participation_fee'],
                'page_title': ''}

    def is_displayed(self):
        return self.round_number == 1

    def before_next_page(self):
        self.player.browser = self.request.META.get('HTTP_USER_AGENT')


class AfterVR(Page):
    form_model = 'player'

    def get_form_fields(self):
        if self.round_number == 1:
            return ['flood_prob', 'water_levels', 'expected_damage']
        elif self.round_number == 2:
            return ['worry', 'trust_dikes', 'concern', 'worry_covid']

    def is_displayed(self):
        return self.round_number <= Constants.num_start_pages


class FinalQuestions(Page):
    form_model = 'player'

    def is_displayed(self):
        return self.round_number >= Constants.num_start_pages + 2

    def before_next_page(self):
        self.player.store_follow_up()

    def get_form_fields(self):
        if self.round_number == 4:
            the_list = []
            if self.player.participant.vars["flooded"] and self.player.participant.vars["mitigated_this_scenario"] < 4:
                the_list.append('regret1')
            elif not self.player.participant.vars["flooded"] and \
                    self.player.participant.vars["mitigated_this_scenario"] == 0:
                the_list.append('regret3')
            else:
                the_list.append('regret2')
            the_list.append('difficult')
            the_list.append('explain_strategy')
            return the_list
        elif self.round_number == 5:
            return['measures', 'other_text']
        elif self.round_number == 6:
            return['perceived_efficacy', 'perceived_cost', 'self_efficacy', 'self_responsibility']
        elif self.round_number == 7:
            return ['clicked_button', 'feedback']


class Scenario(Page):
    form_model = 'player'

    def get_form_fields(self):
        return self.form_fields + ['opened']

    def vars_for_template(self):
        return {'max_payoff': self.participant.vars["max_payoff"]}

    def is_displayed(self):
        return self.round_number == Constants.num_start_pages

    def before_next_page(self):
        self.player.new_scenario_method()


class Instructions(Page):
    form_model = 'player'

    def get_form_fields(self):
        return self.form_fields + ['opened']

    def is_displayed(self):
        return self.round_number == Constants.num_start_pages


class StartScenario(Spelpagina):
    form_model = 'player'
    form_fields = ['opened']

    def before_next_page(self):
        self.player.opened_instructions()

    def is_displayed(self):
        return self.player.in_scenario()

    def vars_for_template(self):
        if self.player.scenario_nr == 0:
            return{'page_title': _('Test scenario')}
        else:
            return{'page_title': _('Final scenario')}


class Check(UnderstandingQuestionsPage):
    page_title = 'Begripsvragen'
    set_correct_answers = False  # APPS_DEBUG
    form_model = 'player'
    form_fields = ['opened']
    form_field_n_wrong_attempts = 'understanding_questions_wrong_attempts'

    def get_questions(self):
        return self.player.get_questions_method()

    def before_next_page(self):
        self.player.opened_instructions()
        self.player.new_scenario_method()

    def is_displayed(self):
        return self.round_number == Constants.num_start_pages + 1


class Decision(Spelpagina):
    form_model = 'player'
    form_fields = ['mitigate']

    def vars_for_template(self):
        vars_for_this_template = self.player.vars_for_invest()
        vars_for_this_template.update({'page_title': _("Investment")})
        return vars_for_this_template

    def before_next_page(self):
        self.player.set_payoff()
        self.player.pay_mitigation_method()
        self.player.opened_instructions()

    def is_displayed(self):
        return self.player.in_scenario()


class Floods(Spelpagina):
    form_model = 'player'
    form_fields = ['opened', 'pay_damage']

    def is_displayed(self):
        return self.player.in_scenario()

    def vars_for_template(self):
        player = self.player
        the_list = {'flood_nrs': player.flood_nrs,
                    'items': models.Constants.items,
                    'items2': models.Constants.items2,
                    'page_title': _('Floods')
                    }
        return the_list

    def before_next_page(self):
        self.player.pay_after_flood()
        self.player.save_payoff()
        self.player.opened_instructions()

        if self.player.flooded:
            self.player.participant.vars["flooded"] = True
        else:
            self.player.participant.vars["flooded"] = False

        if self.player.round_number == Constants.num_start_pages + 1:
            pass
        else:
            self.player.save_final_payoffs()


class Overview(Spelpagina):
    form_model = 'player'

    def vars_for_template(self):
        vars_for_this_template = self.player.vars_for_invest()
        vars_for_this_template.update({'page_title': _('Overview of the past 25 years ')})
        return vars_for_this_template

    def before_next_page(self):
        self.player.opened_instructions()

    def is_displayed(self):
        return self.player.in_scenario()


class Results(Spelpagina):
    form_model = 'player'
    form_fields = ['selected']

    def before_next_page(self):
        self.player.store_instructions()

    def is_displayed(self):
        return self.round_number == Constants.num_start_pages + 2

    def vars_for_template(self):
        vars_for_this_template = self.player.vars_for_payment()
        vars_for_this_template.update({'page_title': ""})
        return vars_for_this_template


class Thanks(Page):
    form_model = 'player'

    def vars_for_template(self):
        return {'page_title': _('Thanks for your participation')}

    def is_displayed(self):
        return self.round_number == Constants.num_rounds


page_sequence = [
    Welcome,
    AfterVR,
    Scenario,
    Instructions,
    StartScenario,
    Decision,
    Floods,
    Overview,
    Check,
    Results,
    FinalQuestions,
    Thanks,
]
