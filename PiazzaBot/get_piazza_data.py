from piazza_api import Piazza
from getpass import getpass
import datetime
import os

class PiazzaWrapper:

    def __init__(self, course_id = 'xxxxxxxxxxx'):
        self.p = Piazza()
        email_id = input("Enter your Piazza email ID : ")
        password = getpass('Piazza Password:')
        # course_id = input("Enter your Course ID : ")
        self.p.user_login(email_id, password)
        user_profile = self.p.get_user_profile()
        self.comp_photo19 = self.p.network(course_id)

    def count_posts(self, posts,today):
        count = 0
        count_i = 0
        count_s = 0
        count_unanswered = 0
        unanswered_posts = []
        for post in posts['feed']:
            if post['type'] == 'question':
                # print(post['nr'])
                # print(post['content_snipet'])
                time = post['log'][0]['t']
                time = datetime.datetime.strptime(time[:-1], "%Y-%m-%dT%H:%M:%S")
                if time.date() == today.date():
                    count += 1
                    if 'has_i' in post.keys():
                        count_i += 1
                    elif 'has_s' in post.keys():
                        count_s += 1
                    else:
                        count_unanswered += 1
                        unanswered_posts.append(post['nr'])
                    # print(time)
        return count, count_i, count_s, count_unanswered, unanswered_posts

    def get_unanswered_followup(self):
        posts = self.comp_photo19.iter_all_posts()
        count = 0
        for post in posts:
            cid = post['nr']
            content = self.comp_photo19.get_post(cid)
            count += self.traverse_content_tree(content)
        return count

    def traverse_content_tree(self, content):
        count = 0
        if 'children' in content.keys():
            if len(content['children'])>0:
                for content_children in content['children']:
                    count += self.traverse_content_tree(content_children)
                    if 'no_answer' in content_children.keys():
                        count += content_children['no_answer']
        return count

    def get_count_today(self):
        posts = self.comp_photo19.get_feed(100,0)
        count, count_i, count_s, count_unanswered, unanswered_posts = self.count_posts(posts,datetime.datetime.today())
        return count, count_i, count_s, count_unanswered, unanswered_posts

if __name__ == '__main__':
    piazza = PiazzaWrapper()
    piazza.get_unanswered_followup()
    piazza.get_count_today()
