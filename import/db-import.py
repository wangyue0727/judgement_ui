# -*- coding: utf-8 -*-

'''
Import the data (assessors, queries, documents) into DB
'''

import os
import re
import sys
import csv
import json
import base64
import argparse
import traceback
import MySQLdb as mdb
import datetime
import codecs
from collections import defaultdict

# global variables
# file paths
# query
ASSESSOR_FILE = 'data/assessor.list'
QUERY_TITLE_FILE = 'data/query-assessor-list.txt'
# ASSESSOR_FILE = 'data/assessor.list'
# QUERY_TITLE_FILE = 'data/query.list'
# document
WARC_CORPUS_FILE = 'data/all-reviews-trec.txt'
DOC_RET_FILE = 'data/appid-reviewid-list.txt'
CATEGORY_FILE = 'data/categories-list.txt'
# WARC_CORPUS_FILE = 'data/corpus.trec'
# DOC_RET_FILE = 'data/ret.list'

# table names
TABLE_TMPL = 'assess_%s'
ASSESSOR_TABLE = TABLE_TMPL % 'assessor'
QUERY_TABLE = TABLE_TMPL % 'query'
DOC_TABLE = TABLE_TMPL % 'document'
ASSESSMENT_TABLE = TABLE_TMPL % 'assessment'
CATEGORY_TABLE = TABLE_TMPL % 'categories'

DB_CON = None

assessor_dict = None
query_dict = None

doc_ret_dict = None
doc_id_dict = dict()

## reverse dict to look up for row-ID in DB
assessor_rev_dict = dict()
query_rev_dict = dict()
query_assessor_rev_dict = dict()
doc_rev_dict = dict()

class MyDB(object) :
  '''
  Configuration of MySQL DB
  '''
  # HOST = '127.0.0.1'
  # PORT = 3306
  # USER = 'xliu'
  # PASSWD = 'who'
  # #DB = 'xliu_cpeg657_14s_1'
  # DB = 'xliu_cpeg657_14s_2'
  HOST = '127.0.0.1'
  PORT = 3306
  USER = 'yuewang'
  PASSWD = 'wangyue0727'
  DB = 'judge'  
  CHAR_SET='utf8'

def load_assessor (file_path) :
  '''
  Load the assessor info

  file_path: string filesystem path to the assessor file
  '''
  try :
    with open(file_path) as assessor_file :
      print '[Info] Loading %s' % file_path

      assessor_dict = dict()
      for line in assessor_file :
        line = line.rstrip()
        # skip comments
        if re.match('#', line) :
          continue
        # skip empty lines
        if re.match(r'^$', line) :
          continue

        row = line.split(' : ')
        if 5 != len(row) :
          print '[Error] Invalid assessor record: %s' % ' : '.join(row)
          continue

        id = row[0]

        item = dict()
        #item['user_id'] = int(row[0])
        item['user_name'] = row[1]
        item['passwd'] = row[2]
        item['full_name'] = row[3]
        assessor_dict[id] = item

      return assessor_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def load_query (file_path) :
  '''
  Load the query title file into a dict

  file_path: string filesystem path to the query file
  '''
  counter=0
  try :
    print '[Info] Loading %s' % file_path
    query_dict = dict()
    #with open(file_path) as query_file :
    query_file = codecs.open(file_path, encoding="utf-8")
    all_text = query_file.read()
    query_lines = all_text.split("\n")
    for line in query_lines :
      # for line in query_file :
      line = line.rstrip()
      # skip comments
      if re.match('#', line) :
        continue
      # skip empty lines
      if re.match(r'^$', line) :
        continue

      row = line.split(' : ')
      if 4 != len(row) :
        # print "Should get 4 elements and actually get %d" % len(row)
        # print line
        print '[Error] Invalid query record: %s' % ' : '.join(row)
        continue

      query_id = row[0]
      assessor_id = row[1]
      query_title = row[2]
      query_desc = row[3]
      # query_desc = query_desc.encode('utf8')
      query_desc = query_desc.replace('\\n', '<br />')


      item = dict()
      item['query_id'] = query_id
      item['assessor_id'] = assessor_id
      item['title'] = query_title
      item['desc'] = query_desc
      query_dict[counter] = item
      counter+=1

    return query_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def load_doc_ret_list (file_path) :
  '''
  Load the retrieval list for query-document map
  '''
  try :
    with open(file_path) as ret_file :
      print 'Loading %s' % file_path

      global doc_id_dict
      doc_ret_dict = defaultdict(dict)
      for line in ret_file :
        line = line.rstrip()
        # skip comments
        if re.match('#', line) :
          continue
        # skip empty lines
        if re.match(r'^$', line) :
          continue

        row = line.split(' ')
        if 3 != len(row) :
          print '[Error] Invalid ret_list record: %s' % ' '.join(row)
          continue

        query_id = row[0]
        doc_id = row[1]
        cnt = int(row[2])

        ## for debug purpose only
        ## select one query only
        #if '1' != query_id :
          #continue

        doc_ret_dict[query_id][doc_id] = 1
        doc_id_dict[doc_id] = 1

      return doc_ret_dict
  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)


def load_trec_corpus (file_path) :
  '''
  Load the corpus in TREC format

  file_path: string filesystem path to the corpus file
  '''
  global DB_CON
  global doc_id_dict

  db_cur = DB_CON.cursor()

  doc_imported = 0
  so_far = 0
  total = os.popen("grep \"<DOC>\" "+WARC_CORPUS_FILE+" | wc -l").read()
  total = int(total.rstrip())

  is_begin = False
  try:
    with open(file_path) as f:
      print '[Info] Loading %s' % file_path

      doc_id = ''
      str_list = []
      for line in f:
        #line = line.strip()
        if re.match(r'<DOC>', line):
          continue
        if re.match(r'<DOCNO>', line):
          mo = re.match(r'<DOCNO>(.+)<\/DOCNO>', line)
          doc_id = mo.group(1)
          continue
        if re.match(r'<TEXT>', line):
          continue
        if re.match(r'<\/TEXT>', line):
          continue
        if re.match(r'<\/DOC>', line):
          so_far += 1
          progress = '\r[%10d / %10d]' % (so_far, total)
          sys.stdout.write(progress)
          sys.stdout.flush()

          # skip documents not in the doc_ret_dict
          if doc_id in doc_id_dict :
            ## import the document to DB
            doc_data = ''.join(str_list)

            if import_doc(db_cur, doc_id, doc_data) :
              doc_imported += 1

          ## clear the list: http://stackoverflow.com/a/850831/219617
          del str_list[:]
          # for debug purpose only
          #if doc_imported >= 500:
            #break

          ## perform commit every 100 documents
          if 0 == doc_imported % 100 :
            do_commit()
            ## for debug purpose only
            #break

        else:
          ## add the current string to str_list
          str_list.append(line)

  except IOError as e:
    print '-' * 60
    print 'Error %d: %s' % (e.args[0],e.args[1])
    traceback.print_exec(file = sys.stdout)
    print '-' * 60
    exit(-1)

  do_commit()
  print '\n[Info] Summary:'
  print '[Info] %d documents imported' % doc_imported

def import_doc(db_cur, doc_id, doc_data) :
  '''
  Import one document to DB
  '''
  global doc_rev_dict


  category, content = extract_category(doc_data)

  title, content = extract_title(content)

  # in rare situation, the title will be blank. We need to fix it.
  if '' == title :
    title = 'N/A'

  title_b64 = base64.b64encode(title)
  sent_id = 't'
  sql = 'INSERT INTO %s(doc_id,sentence_id,data,category) VALUES'\
        '(' % DOC_TABLE
  sql += '%s, %s, %s, %s)'  
  try :
    db_cur.execute(sql, (doc_id, sent_id, title_b64, category))
    # http://stackoverflow.com/a/3790542
    doc_rev_dict[doc_id+"-"+sent_id] = db_cur.lastrowid
  except mdb.Error, e:
    print '[Error] SQL execution: %s' % sql
    print 'Error %d: %s' % (e.args[0],e.args[1])
    return False


  sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', content)
  sent_id = 0
  for sentence in sentences : 

    # sentence_b64 = base64.b64encode(remove_non_ascii(sentence))
    sentence_b64 = base64.b64encode(sentence)
    sql = 'INSERT INTO %s(doc_id,sentence_id,data,category) VALUES'\
          '(' % DOC_TABLE
    sql += '%s, %s, %s, %s)'
    try :
      db_cur.execute(sql, (doc_id, sent_id, sentence_b64, category))
      # http://stackoverflow.com/a/3790542
      doc_rev_dict[doc_id+"-"+str(sent_id)] = db_cur.lastrowid
      sent_id += 1
    except mdb.Error, e:
      print '[Error] SQL execution: %s' % sql
      print 'Error %d: %s' % (e.args[0],e.args[1])
      return False

  return True
  # doc_data_b64 = base64.b64encode(remove_non_ascii(doc_data))

  #print '[Info]: importing %s' % doc_id

  # sql = 'INSERT INTO %s(doc_id,title,data) VALUES'\
  #       '(' % DOC_TABLE
  # sql += '%s, %s, %s)'
  # try :
  #   db_cur.execute(sql, (doc_id, title_b64, doc_data_b64))
  #   # http://stackoverflow.com/a/3790542
  #   doc_rev_dict[doc_id] = db_cur.lastrowid
  #   return True
  # except mdb.Error, e:
  #   print '[Error] SQL execution: %s' % sql
  #   print 'Error %d: %s' % (e.args[0],e.args[1])
  #   return False

def remove_non_ascii(s) :
  '''
  remove non-ASCII characters
  http://stackoverflow.com/a/1342373/219617
  '''
  if not (s is None) :
    return ''.join(filter(lambda x: ord(x)<128, s))
  else :
    return ''

def extract_title(doc) :
  '''
  Extract the title of document
  '''
  title = 'N/A'
  content = ''
  for line in doc.split('\n') :
    if re.match(r'<TITLE>(.+)<\/TITLE>', line):
      mo = re.match(r'<TITLE>(.+)<\/TITLE>', line)
      title = mo.group(1)
      continue
    else : 
      content = content + line 

  return (title, content)

def extract_category(doc) :
  '''
  Extract the category of document
  '''
  category = 'N/A'
  content = ''
  for line in doc.split('\n') :
    if re.match(r'<CATEGORY>', line):
      mo = re.match(r'<CATEGORY>(.+)<\/CATEGORY>', line)
      category = mo.group(1)
      continue
    else : 
      content = content + line + "\n"

  return (category, content)

def test_db() :
  '''
  An example to test the connection of DB
  http://zetcode.com/db/mysqlpython/
  '''
  try :
    con = mdb.connect(host=MyDB.HOST, port=MyDB.PORT, user=MyDB.USER,
        passwd=MyDB.PASSWD, db=MyDB.DB, charset=MyDB.CHAR_SET)
    cur = con.cursor()
    cur.execute('SELECT VERSION()')
    ver = cur.fetchone()
    print '[Info] Database version : %s ' % ver

  except mdb.Error, e:
    print 'Error %d: %s' % (e.args[0],e.args[1])
    sys.exit(1)

  finally :
    if con :
      con.close()

def test() :
  test_db()

def init_db() :
  try :
    global DB_CON
    DB_CON = mdb.connect(host=MyDB.HOST, port=MyDB.PORT, user=MyDB.USER,
        passwd=MyDB.PASSWD, db=MyDB.DB, charset=MyDB.CHAR_SET)
    if DB_CON :
      print '[Info] DB connection initialized'
    else :
      print '[Error] DB connection failed. Will exit.'
      sys.exit(-1)

  except mdb.Error, e:
    print 'Error %d: %s' % (e.args[0],e.args[1])
    if DB_CON :
      DB_CON.close()
    sys.exit(1)

def close_db() :
  global DB_CON
  if DB_CON :
    DB_CON.close()
    DB_CON = None

def sql_execute(cur, sql) :
  '''
  Execute SQL on DB

  cur: the cursor
  sql: the SQL statement
  '''
  try :
    cur.execute(sql)
    return True
  except mdb.Error, e :
    print '[Error] SQL execution: %s' % sql
    print '%d: %s' %(e.args[0], e.args[1])
    return False

def do_commit() :
  '''
  Commit the current transaction
  '''
  try :
    DB_CON.commit()
  except mdb.Error, e :
    print '[Error] Commit - %d: %s' %(e.args[0], e.args[1])
    DB_CON.rollback()
    return False

def load_category (db_cur, file_path) :
  '''
  Load the query title file into a dict

  file_path: string filesystem path to the query file
  '''
  try :
    #with open(file_path) as category_file :
    category_file = codecs.open(file_path, encoding="utf-8")
    print '[Info] Loading %s' % file_path

    category_dict = dict()
    for line in category_file :
      line = line.rstrip()
      # skip comments
      if re.match('#', line) :
        continue
      # skip empty lines
      if re.match(r'^$', line) :
        continue

      row = line.split(' : ')
      if 3 != len(row) :
        print '[Error] Invalid category record: %s' % ' : '.join(row)
        continue

      category = row[0]
      sub_cat_id = row[1]
      key_terms = row[2]
      sql = 'INSERT INTO %s(category,aspect,keywords) VALUES'\
        '(' % CATEGORY_TABLE
      sql += '%s, %s, %s)'  
      try :
        db_cur.execute(sql, (category, sub_cat_id, key_terms))
        # http://stackoverflow.com/a/3790542
      except mdb.Error, e:
        print '[Error] SQL execution: %s' % sql
        print 'Error %d: %s' % (e.args[0],e.args[1])

  except IOError as e :
    print '-' * 60
    traceback.print_exc(file = sys.stdout)
    print '-' * 60
    sys.exit(-1)

def main() :
  init_db()

  #disable import to avoid data been overwritten
  print "Import system is closed to protect the current data"
  return

  global assessor_dict
  global query_dict

  global doc_ret_dict

  global assessor_rev_dict
  global query_rev_dict
  global query_assessor_rev_dict
  global doc_rev_dict

  ## improt assessor
  assessor_dict = load_assessor(ASSESSOR_FILE)
  assessor_id_list = assessor_dict.keys()
  assessor_id_list.sort(key=lambda x: int(x))

  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % ASSESSOR_TABLE
  for id in assessor_id_list :
    user_id = int(id)
    name = assessor_dict[id]['full_name']

    sql = 'INSERT INTO %s(user_id,name) VALUES(%d,' \
        % (ASSESSOR_TABLE, user_id)
    sql += '%s)'
    try :
      db_cur.execute(sql, (name,))
      # http://stackoverflow.com/a/3790542
      assessor_rev_dict[id] = db_cur.lastrowid
    except mdb.Error, e:
      print '[Error] SQL execution: %s' % sql
      print 'Error %d: %s' % (e.args[0],e.args[1])
      sys.exit(-1)

  do_commit()
  # for debug purpose only
  #return



  ## import query
  query_dict = load_query(QUERY_TITLE_FILE)
  query_id_list = query_dict.keys()
  query_id_list.sort(key=lambda x: int(x))

  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % QUERY_TABLE
  for counter in query_id_list :
    query_id = query_dict[counter]['query_id']
    assessor_id = query_dict[counter]['assessor_id']
    title = query_dict[counter]['title']
    desc = query_dict[counter]['desc']
    sql = 'INSERT INTO %s(qid,assessor_id,title,description)'\
        'VALUES(%s,%s,' %(QUERY_TABLE, query_id, assessor_id)
    sql += '%s,%s)'
    try :
      db_cur.execute(sql, (title, desc))
      # http://stackoverflow.com/a/3790542
      query_rev_dict[query_id] = db_cur.lastrowid
      item = dict()
      item['query_id']=query_id
      item['assessor_id']=assessor_id
      item['rowid'] = db_cur.lastrowid
      query_assessor_rev_dict[counter] = item
    except mdb.Error, e:
      print '[Error] SQL execution: %s' % sql
      print 'Error %d: %s' % (e.args[0],e.args[1])
      sys.exit(-1)

  do_commit()
  # for debug purpose only
  #return



  #'''
  ## import documents
  doc_ret_dict = load_doc_ret_list(DOC_RET_FILE)

  sum_num = 0
  print 'Query : # Document statistics'
  for query_id in doc_ret_dict :
    doc_num = len(doc_ret_dict[query_id].keys())
    print '%s : %d' %(query_id, doc_num)
    sum_num += doc_num
  print 'all : %d' % sum_num

  # for debug purpose only
  #return

  print '[Info] Importing %s' % DOC_TABLE
  load_trec_corpus(WARC_CORPUS_FILE)



  ## import assessment table
  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % ASSESSMENT_TABLE
  for query_id in doc_ret_dict :
    if query_id not in query_rev_dict :
      print '[Error] query_id not found in query_rev_dict: %s' % query_id
      continue

    for counter in query_assessor_rev_dict:
      if query_assessor_rev_dict[counter]['query_id'] == query_id:
        # print query_id+", "+query_assessor_rev_dict[counter]['assessor_id']
        assessor_id = query_assessor_rev_dict[counter]['assessor_id']
        query_row_id = query_assessor_rev_dict[counter]['rowid']

        for doc_id in doc_ret_dict[query_id] :
          if doc_id+"-t" not in doc_rev_dict :
            print '[Error] doc_id not found in doc_rev_dict: %s' % doc_id
            continue
          doc_row_id = doc_rev_dict[doc_id+"-t"]

          sql = 'INSERT INTO %s(query_id,document_id,assessor_id,has_assessed,'\
              'relevance,aspect,keywords,doc_bug,assessed_by,last_modified) VALUES(' \
              %(ASSESSMENT_TABLE)
          sql += '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
          try :
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_cur.execute(sql, (query_row_id, doc_row_id, assessor_id, False, 0,
              'N/A', 'N/A', 0,'N/A',now))
          except mdb.Error, e:
            print '[Error] SQL execution: %s' % sql
            print 'Error %d: %s' % (e.args[0],e.args[1])
            sys.exit(-1)
          hasmore = True
          count = 0
          while hasmore:
            if doc_id+"-"+str(count) not in doc_rev_dict :
              hasmore = False
            else:
              doc_row_id = doc_rev_dict[doc_id+"-"+str(count)]

              sql = 'INSERT INTO %s(query_id,document_id,assessor_id,has_assessed,'\
                  'relevance,aspect,keywords,doc_bug,assessed_by,last_modified) VALUES(' \
                  %(ASSESSMENT_TABLE)
              sql += '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
              try :
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                db_cur.execute(sql, (query_row_id, doc_row_id, assessor_id, False, 0,
                  'N/A', 'N/A', 0,'N/A',now))
              except mdb.Error, e:
                print '[Error] SQL execution: %s' % sql
                print 'Error %d: %s' % (e.args[0],e.args[1])
                sys.exit(-1)
              count+=1

  do_commit()

  ## import category table
  db_cur = DB_CON.cursor()
  print '[Info] Importing %s' % CATEGORY_TABLE
  load_category(db_cur,CATEGORY_FILE)

  do_commit()

  return

if '__main__' == __name__ :
  try :
    #test()
    main()
    close_db()
  except KeyboardInterrupt :
    print '\nGoodbye!'

