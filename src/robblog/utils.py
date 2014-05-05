import os
import subprocess 
import roslib
import shutil
from ros_datacentre.message_store import MessageStoreProxy
from robblog.msg import RobblogEntry


def which(program):
    """ Get the path for an executable: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python/377028#377028 """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def init_blog(path):
    """ If path does not exist, create it and init jekyll here """
    if not os.path.isdir(path):
        os.makedirs(path)
        jekyll = which('jekyll')
        if jekyll == None:
            raise Exception('jekyll is not in your path. See README.md for installation instructions.')

        proc = subprocess.Popen([jekyll, 'new', 'robblog'], cwd=path)
        proc.wait()


        path = path + '/robblog'
 
        # now put in default files
        data_path = roslib.packages.get_pkg_dir('robblog') + '/data'
        shutil.copy(data_path + '/_config.yml', path)
        shutil.copy(data_path + '/default.html', path + '/_layouts')

        # and delete the post created by the install
        filelist = os.listdir(path + '/_posts')
        for f in filelist:
            os.remove(path + '/_posts/' + f)

def serve(path, host, port):
    """ Starts jekyll server, return Popen process its runnig in. """
    if not os.path.isdir(path):
        raise Exception('Blog path %s does not exist. Run init_blog with this path first.')
    
    path = path + '/robblog'

    jekyll = which('jekyll')
    if jekyll == None:
        raise Exception('jekyll is not in your path. See README.md for installation instructions.')

    return subprocess.Popen([jekyll, 'serve', '--watch', '--host', host, '--port', port], cwd=path)





class EntryConverter(object):
    """ Converts RobblogEntry objects from message store to markdown posts."""
    def __init__(self, blog_path, collection='message_store', database='message_store'):
        super(EntryConverter, self).__init__()
        # Create some blog entries
        self.post_path = blog_path + '/robblog/_posts/'
        self.msg_store = MessageStoreProxy(collection=collection, database=database)

    
    def convert(self, convert_all=False):
        """ Converts entries without meta['blogged'] == True into markdown posts' """
        entries = self.msg_store.query(RobblogEntry._type)
        blogged_key = 'blogged'
        if convert_all:
            unprocessed = entries
        else:
            unprocessed = [(message, meta) for (message, meta) in entries if blogged_key not in meta or meta[blogged_key] == False]

        for entry, meta in unprocessed:
            file_title = entry.title.replace(' ', '-')
            date = meta['inserted_at']
            file_date = date.strftime("%Y-%m-%d")
            file_name = file_date + '-' + file_title + '.md'
            with open(self.post_path + file_name, 'w+') as f:
                # write file
                f.write('---\nlayout: post\ntitle: %s\n---\n' % entry.title)
                f.write(entry.body)
                f.write('\n')
                f.close()
                # 
                meta[blogged_key] = True
                i = str(meta['_id'])
                self.msg_store.update_id(i, message=entry, meta=meta)
