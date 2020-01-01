from bs4 import BeautifulSoup as bs
from time import perf_counter_ns

import requests, json
import concurrent.futures

class NoUserData(Exception):
    pass
class UserAlreadyExist(Exception):
    pass
class NoFavoritedNovel(Exception):
    pass
class AlreadyFavorited(Exception):
    pass
class FavoriteNovelDoesNotExist(Exception):
    pass
class InvalidNovelTitle(Exception):
    pass

class Reader:
    urlch = 'https://boxnovel.com/novel/{title}/chapter-{chapter}'

    def __init__(self, jsonpath=None):
        self.jsonpath = jsonpath
        self.url = 'https://boxnovel.com/novel/'
        self.urlch = 'https://boxnovel.com/novel/{title}/chapter-{chapter}'

        self.getuser = self.updatejson(self.getuser)
        self.user = self.updatejson(self.user)
        self.favorites = self.updatejson(self.favorites)
        self.newFavorite = self.updatejson(self.newFavorite)
        self.update = self.updatejson(self.update)
        self.removeFavorite = self.updatejson(self.removeFavorite)
        self.read = self.updatejson(self.read)
        self.update = self.timeit(self.update)

        try:
            with open(self.jsonpath, 'r') as rf:
                self.data = json.load(rf)
        except:
            with open(self.jsonpath, 'w') as wf:
                data = []
                json.dump(data, wf)

    def timeit(self, func):
        def f(*args, **kwargs):
            start = perf_counter_ns()
            rv = func(*args, **kwargs)
            end = perf_counter_ns()
            print(f'time taken: {end - start}')
            return rv
        return f
        
    def updatejson(self, func):
        def f(*args, **kwargs):
            with open(self.jsonpath, 'r') as rf:
                self.data = json.load(rf)
            return func(*args, **kwargs)
        return f

    def getuser(self, id):
        for user in self.data:
            for key, val in user.items():
                if key == 'id':
                    if val == int(id):
                        return user
        return None

    def newFavorite(self, id, title, lastreadchapter=1):
        if user := self.getuser(id):
            if title in [novel['title'] for novel in user['favorites']]:
                raise AlreadyFavorited
            else:
                user['favorites'].append(
                    {
                        'title': title,
                        'lastreadchapter': lastreadchapter,
                        'latestchapter': 'tbu'
                    }
                )
                with open(self.jsonpath, 'w') as wf:
                    json.dump(self.data, wf)
                return f'{title} added to Favorites'
        raise NoUserData

    def newUser(self, id, username=''):
        if self.getuser(id):
            raise UserAlreadyExist
        else:
            self.data.append({
                "id": int(id),
                "username": username,
                "favorites": []
            })
            with open(self.jsonpath, 'w') as wf:
                json.dump(self.data, wf)
            return f'{(username if username != "" else id)} user added!'
    
    def user(self, id):
        if user := self.getuser(id):
            text = f'Hello {(user["username"] if user["username"] != "" else user["id"])}!\nYour Favorite Novels are:\n'
            text += ', '.join([novel['title'] for novel in user['favorites']])
            return text
        raise NoUserData

    def removeFavorite(self, id, title):
        if user := self.getuser(id):
            exist = False
            index = -1
            for i, novel in enumerate(user['favorites']):  
                if novel['title'].lower() == title.lower():
                    index = i
                    exist = True
                    break
            if not exist:
                raise FavoriteNovelDoesNotExist(title)
            else:
                print(user['favorites'].pop(index))
                with open(self.jsonpath, 'w') as wf:
                    json.dump(self.data, wf)
                return f'<{novel["title"]}> is now removed from your favorites.'
        raise NoUserData

    def update(self, id):
        if user := self.getuser(id):
            rv_u = 'Title\t\tPreviousLatest\t\tLatest\t\n'
            rv_n = 'Title\t\tStillLatest\n'

            titles = [novel['title'] for novel in user['favorites']]
            platests = [novel['latestchapter'] for novel in user['favorites']]
            ftitles = list(map(lambda title: title.lower().replace(' ', '-'), titles))
            latests = processChapters(ftitles)
            for i, novel in enumerate(user['favorites']):
                novel['latestchapter'] = latests[i]
                if platests[i] != latests[i]:
                    rv_u += f'{titles[i][:8]}\t\t{platests[i]}\t\t{latests[i]}\n'
                else:
                    rv_n += f'{titles[i][:8]}\t\t{latests[i]}\n'
            with open(self.jsonpath, 'w') as wf:
                json.dump(self.data, wf)
            return rv_u + '\n' + rv_n

            # for novel in user['favorites']:
            #     title = novel['title'].lower()
            #     orig_title = title[:]
            #     title = title.replace("'", '').replace(' ', '-')
            #     lastread = novel['lastreadchapter']
            #     latest_chapter = novel['latestchapter']
            #     page = requests.get(self.urlch.format(title=title, chapter=lastread))
            #     soup = bs(page.text, 'html.parser')
            #     soup = soup.find(class_='selectpicker single-chapter-select')
            #     if soup is None:
            #         raise InvalidNovelTitle(orig_title)

            #     # soups = str(soup)
            #     # value_index = soups.rfind('value="') + 7
            #     # new_latest_chapter = self.getnum(soups[value_index:soups.find('"', value_index)])

            #     soup = soup.find_all('option')
            #     lastoption = str(soup.pop())
            #     value_index = lastoption.find('value="') + 7
            #     new_latest_chapter = self.getnum(lastoption[value_index:lastoption.find('"', value_index)])

            #     novel['latestchapter'] = new_latest_chapter
            #     if latest_chapter != new_latest_chapter:
            #         rv_u += f'{orig_title[:8]}\t\t{latest_chapter}\t\t{new_latest_chapter}\n'
            #     else:
            #         rv_n += f'{orig_title[:8]}\t\t{new_latest_chapter}\n'
            # with open(self.jsonpath, 'w') as wf:
            #     json.dump(self.data, wf)
            # return rv_u + '\n' + rv_n
        else:
            raise NoUserData
        
    def favorites(self, id):
        if user := self.getuser(id):
            if len(user['favorites']) != 0:
                rv = f'{"Title":^15}\t\tRead\t\tLatest\n'
                for novel in user['favorites']:
                    title = novel['title']
                    read = novel['lastreadchapter']
                    latest = novel['latestchapter']
                    rv += f'{title[:8]}\t\t{read:*>4}\t\t{str(f"{latest:*>4}"):>6}\n'
                return rv
            raise NoFavoritedNovel
        raise NoUserData
    
    def read(self, id, title, chapter=None):
        if user := self.getuser(id):
            favorites = user['favorites']
            for novel in favorites:
                if novel['title'].lower() == title.lower():
                    lastread = novel['lastreadchapter']
                    toread = lastread+1 if chapter in ['next', 'Next'] else chapter if type(chapter) == int else lastread
                    ftitle = title.lower().replace(' ', '-')
                    page = requests.get(self.urlch.format(title=ftitle, chapter=toread))
                    soup = bs(page.text, 'html.parser')
                    soup = soup.find(class_='text-left')
                    if soup == None:
                        raise InvalidNovelTitle
                    rv = (soup.find_all('p'))
                    rv = list(map(lambda p: p.text, rv))
                    novel['lastreadchapter'] = toread
                    with open(self.jsonpath, 'w') as wf:
                        json.dump(self.data, wf)
                    return rv
            raise FavoriteNovelDoesNotExist
        raise NoUserData

    @staticmethod
    def getnum(s):
        rv = ''
        for c in s:
            try:
                int(c)
                rv += c
            except:
                pass
        return int(rv)

def getLatest(title):
    page = requests.get(Reader.urlch.format(title=title, chapter=1))
    soup = bs(page.text, 'html.parser')
    soup = soup.find(class_='selectpicker single-chapter-select')
    if soup is None:
        raise InvalidNovelTitle(title)
    soup = soup.find_all('option')
    lastoption = str(soup.pop())
    value_index = lastoption.find('value="') + 7
    latest = Reader.getnum(lastoption[value_index:lastoption.find('"', value_index)])
    return latest

def processChapters(titles):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(getLatest, titles)
        return list(results)

if __name__ == "__main__":
    reader = Reader('./users.json')
    # print(reader.read(2652809561493301, 'Library of Heavens Path'))
    print(reader.update(2652809561493301))
    # print(reader.removeFavorite(26528095614933011, "library of heavens path"))
    # reader.newFavorite(2549683768461400, 'Solo Leveling2')