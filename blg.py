from __future__ import absolute_import

import argparse
import os
import re
import sys
import time

from googleapiclient import discovery
from googleapiclient.http import build_http
from oauth2client import client
from oauth2client import file
from oauth2client import tools

### configure the service
### API Blogger-v3
### Get OAuth 2.0 client key from Google console
### get blogID from your blog url
def SERVICE_NAME(): return 'blogger'
def VERSION(): return 'v3'
def CLIENT_SECRET(): return 'client_secret.json'
def SCOPE(): return 'https://www.googleapis.com/auth/blogger'
###
### other configure 
def TAG_FILE(): return 'tag_record'
def MAX_RESULTS(): return 500


class BlgService(object):
	def __init__(self):
		### connect to the service
		flow = client.flow_from_clientsecrets(CLIENT_SECRET(), scope = SCOPE(), message = tools.message_if_missing(CLIENT_SECRET()))
		storage = file.Storage(SERVICE_NAME() + '.dat')
		credentials = storage.get()
		print('sss', tools.argparser)
		parser = argparse.ArgumentParser(parents=[tools.argparser])
		flags = parser.parse_args('')
		print('sss',flags)
		if credentials is None or credentials.invalid:

			credentials = tools.run_flow(flow, storage, flags)
		http = credentials.authorize(http=build_http())
		self.service = discovery.build(SERVICE_NAME(), VERSION(), http = http)
		###

		### get user information 
		user_info = self.service.users().get(userId='self').execute()
		self.userId = user_info['id']
		print('Hello ' + user_info['displayName'] + '! Get your userId associated with your client_secret.json')
		###

		### set blogId
		self.blogId = False
		###

	def set_blog_id(self, blog_num):
		### get blogId
		blogs_info = self.service.blogs().listByUser(userId=self.userId).execute()
		if len(blogs_info['items']) > 1 and blog_num < 0:
			print('Please specify your blogId, becuase you have multiple blogs')
			for i in range(len(blogs_info['items'])):
				print(i, ':', blogs_info['items'][i]['name'])
			os._exit(1)
		blog_num = max(blog_num, 0)
		self.blogId = blogs_info['items'][blog_num]['id']
		###
		return self.blogId

	def set_post_id(self, draft_num, status):
		if status is None:
			status_txt = 'post'
		else:
			status_txt = status
		### get postId
		if self.blogId is False:
			print('[inner error] Cannot get [' + status_txt + '] without blogId at set_draft_id')
			os._exit(1)


		drafts_info = self.service.posts().list(blogId=self.blogId, status=status, maxResults=MAX_RESULTS()).execute()
		if len(drafts_info['items']) > 1 and draft_num < 0:
			print('Please specify your postId for [' + status_txt + '], becasue you have multiple [' + status_txt + ']')
			for i in range(len(drafts_info['items'])):
				print(i, ':', drafts_info['items'][i]['title'])
			os._exit(1)
		draft_num = max(draft_num, 0)
		postId = drafts_info['items'][draft_num]['id']
		###
		return postId

	def update_tags(self, tags, request):
		response = request.execute()
		for i in response['items']:
			if 'labels' not in i:
				continue
			for j in i['labels']:
				if j not in tags:
					tags[j] = 1
		return response

	
		

class Blg(object):
	def __init__(self):
		parser = argparse.ArgumentParser(usage='''
	blg <action> [<args>]

	blg actions are:
		insert\tPost an html file as draft
		publish\tPublish a draft
		tag\tManage your tags
		revert\tUnpublish the post
		update\tUpdate the post and make it as draft
			''')

		parser.add_argument('action', help='Action you want to make')
		args = parser.parse_args(sys.argv[1:2])
		if not hasattr(self, args.action):
			print('Unrecognized action')
			parser.print_help()
			os._exit(1)
		getattr(self, args.action)()

	def insert(self):
		parser = argparse.ArgumentParser(
		    description='Post your html to your blog as draft')
		# prefixing the argument with -- means it's optional
		parser.add_argument('--blog_idx', type=int, default=-1)
		parser.add_argument('--tag', type=str, default='', help='TAG1,TAG2,...')
		parser.add_argument('infile', help='Html you want to post')
		parser.add_argument('title', help='Draft title')
		args = parser.parse_args(sys.argv[2:])
		print('Running blg insert, blog_idx=%s, tag=%s' % (args.blog_idx, args.tag))

		service_object = BlgService()
		service_object.set_blog_id(args.blog_idx)
		### post as draft
		try:
			f = open(args.infile, 'r')
		except FileNotFoundError:
			print(args.infile + ' does not exist! Please try again.')
			sys.exit()
		if args.tag != '':
			labels = args.tag.split(',')
		body = {'content': f.read(), 'title': args.title, 'labels': labels}
		post = service_object.service.posts().insert(blogId=service_object.blogId, body=body, isDraft=True).execute()
		print('The file: ' + post['title'])
		print('is posted as draft at: ' + post['url'])
		print('To make your latest draft publish, try blg publish')
		###

	def publish(self):
		parser = argparse.ArgumentParser(
		    description='Publish your draft')
		parser.add_argument('--blog_idx', type=int, default=-1)
		parser.add_argument('--draft_idx', help='The draft you want to publish', type=int, default=-1)
		args = parser.parse_args(sys.argv[2:])
		print('Running blg publish, blog_idx=%s, draft_idx=%s' % (args.blog_idx, args.draft_idx))

		service_object = BlgService()
		service_object.set_blog_id(args.blog_idx)
		postId = service_object.set_post_id(args.draft_idx, 'draft')
		post = service_object.service.posts().publish(blogId = service_object.blogId, postId = postId).execute()
		print('The file: ' + post['title'])
		print('is published at: ' + post['url'])

	def tag(self):
		'''
		It is handy for managing your blog by controlling your tags and keeping them consistant. 
		This function goes through all your existing labels right now and write the results to tags.txt locally.
		The tag.txt follows the format:
		#s--- Write time1 ---#
		TAG1\tyour can add comment if you like
		TAG2
		TAG3
		#e
		#s--- Write time2 ---#
		TAG1\tyour can add comment if you like
		TAG2
		TAG3
		TAG4
		#e
		'''
		parser = argparse.ArgumentParser(
		    description='Maintain tag.txt locally')
		parser.add_argument('do', choices=['update', 'print'], help='update or print latest tag update')
		parser.add_argument('--blog_idx', type=int, default=-1)
		args = parser.parse_args(sys.argv[2:])
		print('Running blg tag blog_idx=%s' % args.blog_idx)


		service_object = BlgService()
		service_object.set_blog_id(args.blog_idx)
		tag_file_name = TAG_FILE() + '.' + str(service_object.blogId) + '.txt'
		
		if args.do == 'update':
			tagfile = open(tag_file_name, 'a')
			localtime = time.asctime( time.localtime(time.time()) )
			tagfile.write('#s--- ' + localtime + ' ---#\n')
			tags = {}
			request = service_object.service.posts().list(blogId=service_object.blogId, maxResults=MAX_RESULTS())
			service_object.update_tags(tags, request)
			for j in tags.keys():
				tagfile.write(j + '\n')
			tagfile.write('#e\n')
		elif args.do == 'print':
			try:
				tagfile = open(tag_file_name, 'r')
			except FileNotFoundError:
				print(tag_file_name + ' does not exist yet. Please do blg tag update!')
				os._exit(1)
			myread = tagfile.readlines()
			nlines = len(myread)
			pos = nlines - 1
			tags = []
			while pos >= 0:
				if ''.join(myread[pos][0:5]) == '#s---':
					break
				else:
					if ''.join(myread[pos][0:2]) != '#e':
						tags.append(myread[pos].strip())
				pos -= 1
			for i in reversed(tags):
				print(i)

	def revert(self):
		parser = argparse.ArgumentParser(
		    description='Revert your published post as draft')
		parser.add_argument('--blog_idx', type=int, default=-1)
		parser.add_argument('--published_idx', help='The post you want to revert', type=int, default=-1)
		args = parser.parse_args(sys.argv[2:])
		print('Running blg revert, blog_idx=%s, published_idx=%s' % (args.blog_idx, args.published_idx))

		service_object = BlgService()
		service_object.set_blog_id(args.blog_idx)
		postId = service_object.set_post_id(args.published_idx, 'live')

		post = service_object.service.posts().revert(blogId=service_object.blogId, postId=postId).execute()
		print('The file: ' + post['title'])
		print('is reverted as draft from: ' + post['url'])

	def update(self):
		parser = argparse.ArgumentParser(
		    description='Update your post and set it as draft')
		parser.add_argument('--infile', help='If change html')
		parser.add_argument('--title', help='If change title')
		parser.add_argument('--tag', type=str, default='', help='If change tag')
		parser.add_argument('--blog_idx', type=int, default=-1)
		parser.add_argument('--post_idx', help='The post you want to revert', type=int, default=-1)
		args = parser.parse_args(sys.argv[2:])
		print('Running blg update, blog_idx=%s, post_idx=%s, infile=%s, title=%s, tag=%s' % (args.blog_idx, args.post_idx, args.infile, args.title, args.tag))

		service_object = BlgService()
		service_object.set_blog_id(args.blog_idx)
		postId = service_object.set_post_id(args.post_idx, None)
		post_idx = max(args.post_idx, 0)
		post_list = service_object.service.posts().list(blogId=service_object.blogId, maxResults=post_idx + 1).execute()
		this_post = post_list['items'][post_idx]
		
		if args.infile:
			try:
				content = open(args.infile, 'r')
				content = content.read()
			except FileNotFoundError:
				print(args.infile + ' does not exist! Please try again.')
				os._exit(1)
		else:
			content = this_post['content']

		if args.tag != '':
			labels = args.tag.split(',')
		else:
			labels = this_post['labels']

		if args.title:
			title = args.title
		else:
			title = this_post['title']

		body = {'content': content, 'title': title, 'labels': labels}
		post = service_object.service.posts().update(blogId=service_object.blogId, postId=postId, body=body).execute()
		print('The file: ' + post['title'])
		print('is posted as draft at: ' + post['url'])
		print('To make your latest draft publish, try blg publish')



if __name__ == '__main__':
	Blg()
	