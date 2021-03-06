# -*- coding: utf-8 -*-
import urllib.request
import json
import logging
import hashlib
import os
import base64


class pyCoUpdater:

    def __init__(self, cli, ev, conf, bot):
        self.bot = bot
        self.cli = cli
        self.conf = conf
        self.ev = ev
        self.githttpupd = {}
        self.gitupd = {}
        self.gitupdrepos = {}
        self.upd = False
        self.restartupd = False

    def addfile(self, utype, module, user="", repo="", url=""):
        if utype == "github":
            # TODO: Actualizador vía github api
            try:
                self.gitupd[user + "/" + repo]
            except KeyError:
                self.gitupd[user + "/" + repo] = []
            self.gitupd[user + "/" + repo].append(module)
        elif utype == "github-http":
            try:
                self.githttpupd[user + "/" + repo]
            except KeyError:
                self.githttpupd[user + "/" + repo] = []
            self.githttpupd[user + "/" + repo].append(module)
        elif utype == "http":
            pass  # TODO: Actualizador vía http normal

    def update(self):
        self.preprocessgithttp()
        self.modrepos()
        self.coreupdate()

        if self.upd is False:
            self.cli.msg(self.ev.target,
                self.bot._(self.ev, 'core', 'update.noupdate'))
        print("updend")
        return self.restartupd

    def modrepos(self):
        for x, xval in enumerate(self.conf.get('modulerepos')):
            if xval['autodownload'] is True:
                ix = urllib.request.urlopen('https://github.com/%s/ra' % (xval[
                 'location']) + 'w/master/index.json').read()
                index = json.loads(ix.decode('utf-8'))
                for x, val in enumerate(index['modules']):
                    try:
                        open("modules/%s/%s.py" % (val, val))
                    except:
                        val = "modules/%s/%s" % (val, val)
                        if self.processgit(xval['location'], val + ".py") \
                         is True:
                            self.processgit(xval['location'], val + ".json")
                            self.upd = True
                            foobar = json.load(open("modules/" + val + "/" +
                            val + ".json"))
                            try:
                                for f1 in foobar['files']:
                                    self.processgit(xval['location'],
                                            "modules/" + val + "/" + f1)
                            except:
                                pass

                            #self.cli.msg(self.ev.target,
                            #    self.bot._(self.ev, 'core', 'update.newfile')
                            #        .format(val))

    def coreupdate(self):
        # TODO: Descargar archivos nuevos
        self.processgit("irc-CoBot/pyCoBot", "pycobot/index.json")
        ix = open("pycobot/index.json").read()
        index = json.loads(ix)
        for x, xval in enumerate(index):
            if self.processgit("irc-CoBot/pyCoBot", "pycobot/" + xval) is \
             True:
                self.upd = True
                self.restartupd = True

        # \o/
        if self.processgit("irc-CoBot/pyCoBot", "pycobot.py") is True:
            self.upd = True
            self.restartupd = True
        if self.processgit("irc-CoBot/pyCoBot", "irc/client.py") is True:
            self.upd = True
            self.restartupd = True

    def preprocessgithttp(self):
        # TODO: Auto-descarga de módulos no encontrados localmente
        for i in enumerate(self.gitupd):
            i = i[1]
            logging.info("Descargando indice de modulos para el " +
            "repositorio %s" % i)
            ix = urllib.request.urlopen('https://github.com/%s/raw' % i +
             '/master/index.json').read()  # Obtenemos el indice de modulos..
            index = json.loads(ix.decode('utf-8'))
            for k, val in enumerate(self.gitupd[i]):
                for x, xval in enumerate(index['modules']):
                    if val == xval:
                        self.processgit(i, "modules/" + val + "/" + val +
                         ".json")
                        foobar = json.load(open("modules/" + val + "/" + val +
                         ".json"))
                        try:
                            for f1 in foobar['files']:
                                self.processgit(i, "modules/" + val + "/" +
                                                    f1)
                        except:
                            pass
                        if self.processgit(i, "modules/" + val + "/" + val +
                         ".py") is True:
                            #self.cli.msg(self.ev.target,
                            #    self.bot._(self.ev, 'core', 'update.file')
                            #        .format("modules/" + val))
                            self.upd = True
                            try:
                                # si esta cargado...
                                self.bot.modinfo[val]
                                # ... lo recargamos...
                                self.bot.unloadmod(val)
                                self.bot.loadmod(val, self.cli)
                            except:
                                pass  # ???

    def processgit(self, repo, path):
        try:
            self.gitupdrepos[repo]
        except:
            response = self.gitHttpRequest("https://api.github.com/repos/"
            "{0}/git/trees/master?recursive=1".format(repo)).read().decode()
            self.gitupdrepos[repo] = json.loads(response)

        for f in self.gitupdrepos[repo]['tree']:
            if f['path'] == path:
                if not self.compHash(path, f['sha']):
                    response = self.gitHttpRequest(f['url']).read().decode()
                    response = json.loads(response)
                    ensure_dir(path)
                    open(path, "w").write(base64.b64decode(response['content'].encode()).decode())
                    self.cli.msg(self.ev.target,
                        self.bot._(self.ev, 'core', 'update.file').format(path))
                    logging.info("Actualizando %s." % (path))
                    return True
        return False

    def gitHttpRequest(self, url):
        r = urllib.request.Request(url)
        u = self.bot.readConf("config.github.user", default=False)
        p = self.bot.readConf("config.github.password", default=False)
        if u is not False and p is not False:
            b6 = base64.b64encode("{0}:{1}".format(u, p).encode()).decode()
            r.add_header("Authorization", "Basic {0}".format(b6))
        return urllib.request.urlopen(r)

    def compHash(self, path, chash):
        try:
            f = open(path).read()
        except:
            return False
        v = "blob {0}\0{1}".format(len(f.encode('utf-8')), f)
        fhash = hashlib.sha1(v.encode()).hexdigest()
        if fhash == chash:
            return True
        else:
            return False

    def processgithttp(self, repo, path):
        response = urllib.request.urlopen('https://github.com/%s/raw' % (repo) +
        '/master/%s' % path).read()
        try:
            f = open(path, "rb")
            fh = hashlib.sha1(f.read()).hexdigest()
            f.close()
        except:
            fh = 0

        oh = hashlib.sha1(response).hexdigest()
        if not fh == oh:
            logging.info("Actualizando %s. Hash local: %s. Hash remoto: %s" % (
             path, fh, oh))

            ensure_dir(path)
            f = open(path, "wb")
            f.write(response)
            f.close()
            self.cli.msg(self.ev.target,
                self.bot._(self.ev, 'core', 'update.file').format(path))
            return True
        else:
            return False


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)
