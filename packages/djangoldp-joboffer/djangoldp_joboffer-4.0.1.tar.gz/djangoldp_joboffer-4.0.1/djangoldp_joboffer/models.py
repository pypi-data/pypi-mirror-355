import requests
import re
from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from djangoldp.activities import ActivityQueueService
from djangoldp.models import Model, Activity
from djangoldp.permissions import AnonymousReadOnly, ReadAndCreate, OwnerPermissions, InheritPermissions
from djangoldp_community.models import Community
from djangoldp_skill.models import Skill
from djangoldp_conversation.models import Conversation
from djangoldp_notification.models import Notification, Subscription, get_default_email_sender_djangoldp_instance
from djangoldp_notification.views import filter_object_is_permitted

job_fields = ["@id", "author", "title", "description", "creationDate", "skills", "budget", "duration", "location",\
    "earnBusinessProviding", "closingDate", "conversation"]
if 'djangoldp_community' in settings.DJANGOLDP_PACKAGES:
    job_fields += ['community']


class JobOffer(Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='jobOffers', on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    #TODO: set cascade. For now we allow the deletion of groups while keeping the joboffers
    community = models.ForeignKey(Community, related_name="joboffers", on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.CharField(max_length=255, blank=True, null=True)
    budget = models.CharField(max_length=255, blank=True, null=True)
    earnBusinessProviding = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True, null=True)
    skills = models.ManyToManyField(Skill, blank=True)
    creationDate = models.DateTimeField(auto_now_add=True)
    closingDate = models.DateField(null=True)
    conversation = models.ManyToManyField(Conversation, blank=True)

    class Meta:
        auto_author = 'author'
        owner_field = 'author'
        nested_fields = ["skills", "conversation"]
        permission_classes = [AnonymousReadOnly, InheritPermissions, ReadAndCreate|OwnerPermissions]
        inherit_permissions = ['community']
        container_path = 'job-offers/'
        serializer_fields = job_fields
        rdf_type = 'hd:joboffer'

    # functions used in notification of JobOffer to users
    #  https://git.startinblox.com/djangoldp-packages/djangoldp-notification
    def serialize_notification(self) -> None:
        '''serializes into a JSON-LD object for package djangoldp-notification'''
        return {
            '@id': self.urlid,
            '@type': getattr(JobOffer._meta, 'rdf_type', 'hd:joboffer'),
            'title': self.title,
            'description': self.description,
            'duration': self.duration,
            'location': self.location,
            'budget': self.budget,
            'closingDate': str(self.closingDate),
            'skills': {
                '@type': 'ldp:Container',
                'ldp:contains': ','.join(self.skills.all().values_list('urlid', flat=True))
            }
        }

    @classmethod
    def permit_notification(cls, target, notification):
        from djangoldp_joboffer.notifications import filter_joboffer_notification_recipient_has_skill
        
        return filter_joboffer_notification_recipient_has_skill(target, notification)

    def __str__(self):
        try:
            return '{} -> {} ({})'.format(self.author.urlid, self.title, self.urlid)
        except:
            return self.urlid


def to_text(html):
  return re.sub('[ \t]+', ' ', strip_tags(html)).replace('\n ', '\n').strip()


@receiver(post_save, sender=JobOffer)
def send_mail_to_fnk(instance, created, **kwargs):
    if created and instance.earnBusinessProviding:
        if getattr(settings, 'JOBOFFER_SEND_MAIL_BP', False):
            email_from = get_default_email_sender_djangoldp_instance()

            if email_from is None:
                return

            message_html = render_to_string('joboffer/email.html', {
                "instance": instance,
                "fnk": True
            })
            send_mail(
                "Une nouvelle offre demande un apport d'affaire",
                to_text(message_html),
                email_from,
                getattr(settings, 'JOBOFFER_SEND_MAIL_BP'),
                fail_silently = True,
                html_message = message_html
            )

@receiver(post_save, sender=Notification)
def send_email_on_notification(sender, instance, created, **kwargs):
    if created \
            and instance.user.email \
            and instance.type == 'JobOffer':

        email_from = get_default_email_sender_djangoldp_instance()

        if email_from is None or not instance.user.settings.receiveMail:
            return

         # get author name, and store in who
        try:
            # local author
            if instance.author.startswith(settings.SITE_URL):
                who = str(Model.resolve_id(instance.author.replace(settings.SITE_URL, '')).get_full_name())
            # external author
            else:
                who = requests.get(instance.author).json()['name']
        except:
            who = "Quelqu'un"

        on = str(getattr(settings, 'INSTANCE_DEFAULT_CLIENT', False)) \
            + '/job-offers/job-offers-detail/@' + instance.object + '@'

        joboffer = JobOffer.objects.get(urlid=instance.object)
        message_html = render_to_string('joboffer/email.html', {
            "instance": joboffer,
            "fnk": False,
            "author": who,
            "on": on
        })

        send_mail(
            "Une nouvelle offre pourrait t'intéresser",
            to_text(message_html),
            email_from,
            [instance.user.email],
            fail_silently = False,
            html_message = message_html
        )

@receiver(m2m_changed, sender=JobOffer.skills.through, dispatch_uid='notify_job')
def send_joboffer_notifications(instance, model, pk_set, action, **kwargs):
    # This signal is fired when a local JobOffer has been saved
    # and a sequence of skills have finished being added to it
    # The intention is that a notification will be dispatched to all "connected users" with matching skills
    if getattr(settings, 'ENABLE_JOBOFFER_NOTIFICATIONS', True) \
        and not Model.is_external(instance) and action == 'post_add':
        if model==JobOffer: #if the signal is triggered by a change on the skill
            for joboffer in JobOffer.objects.filter(pk__in=pk_set):
                notify_job(joboffer)
        else:
            notify_job(instance)

def notify_job(joboffer):
    # build the notification data
    notification_obj = joboffer.serialize_notification()
    notification_type = "JobOffer"
    author = getattr(joboffer.author, "urlid", str(_("Auteur inconnu")))
    summary = joboffer.description if joboffer.description is not None else ''
    notification = {
        "@context": settings.LDP_RDF_CONTEXT,
        "object": notification_obj,
        "author": author,
        "type": notification_type,
        "summary": summary
    }

    # The first part of "connected users" are all users local to this joboffer
    # who have not been notified about this JobOffer before
    prior_notified_users = Notification.objects.filter(object=joboffer.urlid).values_list('user', flat=True)
    for recipient in get_user_model().objects.exclude(pk__in=prior_notified_users):
        # if the recipient has an appropriate skill for the joboffer
        if not get_user_model().is_external(recipient) and recipient.urlid != author and filter_object_is_permitted(recipient, notification):
            Notification.objects.create(user=recipient, object=joboffer.urlid, author=author, type=notification_type, summary=summary)

    # The second part of "connected users" is related to our dependency djangoldp_notification
    # all subscriptions which target /job-offers/ will be sent notifications to their configured inbox
    # if the inbox is configured to /job-offers/inbox/ (a url provided by this package), a notification will be sent to all users on that server with appropriate skills
    targets = Subscription.objects.filter(object='{}{}'.format(settings.SITE_URL, JobOffer.get_container_path()))
    for target in targets:
        if not Activity.objects.filter(external_id = target.inbox, payload__contains=joboffer.urlid).exists():
            #Do not send the activity twice
            ActivityQueueService.send_activity(target.inbox, notification)
