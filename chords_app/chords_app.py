from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.treeview import TreeView, TreeViewNode
from kivy.uix.treeview import TreeViewLabel
from kivy.uix.listview import ListView
from kivy.uix.scrollview import ScrollView
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
import sqlite3
import os, HTMLParser
from kivy.app import App
from pdb import set_trace
from kivy.lang import Builder
import re
Builder.load_string(
'''
<TextInput>
    canvas.before:
        Color:
            rgba: 0,0,0,1
''')
POSdb = "../songs_singers.db"

class TreeViewButton(TextInput, TreeViewNode, ScrollView):
    pass

modGroups = []
modItems = []
modNumbers = []
modType = []
modWords = {}
modDict = dict()
modDictUnique = dict()
modDictNumGrp = dict()
# modDictTypeNum = dict()
h=HTMLParser.HTMLParser()

def populate_tree_view(tv):
    conn = sqlite3.connect(POSdb)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('select * from songs')
    r = c.fetchall()
    for entry in r:
        modGroups.append(entry['rus_name'])
        modItems.append(entry['song_name'])
        modNumbers.append(entry['page_num'])
        # modType.append(entry['type'])
        modWords.update({entry['song_name']: entry['song_words']})
        # modWords.append(entry['song_words'])
    modDict = zip(modGroups, modItems)
    for m, n in modDict:
        if m not in modDictUnique:
            modDictUnique[m] = [n]
        else:
            modDictUnique[m].append(n)
    sortedGroups = modDictUnique.keys()
    sortedGroups.sort()

    modNumGrp = zip (modNumbers, modGroups)
    for k, v in modNumGrp:
        if k not in modDictNumGrp:
            modDictNumGrp[k] = [v]
        else:
            modDictNumGrp[k].append(v)
    sortedNumbers = modDictNumGrp.keys()
    sortedNumbers = sorted(sortedNumbers, key=int)

    # modTypeNum = zip(modType, modNumbers)
    # for k, v in modTypeNum:
    #     if k not in modDictTypeNum:
    #         modDictTypeNum[k] = [v]
    #     else:
    #         modDictTypeNum[k].append(v)
    # sortedTypes = modDictTypeNum.keys()
    # sortedTypes.sort()

    #print modItems
    #print modDictUnique
    # for type in sortedTypes:
    #     k = tv.add_node(TreeViewLabel(text='%s' % type))#, is_open=True))
    #     print "ITERATION"
    for number in sortedNumbers[:3]:
        # n = tv.add_node(TreeViewLabel(text='%s' % number), k)#, is_open=True))
        n = tv.add_node(TreeViewLabel(text='%s' % number))#, is_open=True))
        for group in modDictNumGrp[number]:
            g = tv.add_node(TreeViewLabel(text='%s' % group), n)
            for item in modDictUnique[group]:
                p = tv.add_node(TreeViewLabel(text='%s' % item), g)
                # c.execute("select song_words from songs where song_name = '%s'"%p)
                # words = c.fetchall()
                # tv.add_node(TreeViewButton(text='%s'%words), p)
                #set_trace()
                tv.add_node(TreeViewButton(text=h.unescape(re.compile('\r\n').sub('\n','%s'%modWords[item])), color_selected=[256,256,256,1], is_leaf=True, no_selection=False, height = 600), p)


class POSFM(App):
    def build(self):
        tv = TreeView(root_options=dict(text='Tree One'),
                      hide_root=True,
                      indent_level=4)

        #
        # root = ScrollView(size_hint=(None, None), size=(400, 400),
        #     pos_hint={'center_x':.5, 'center_y':.5})
        # root = ScrollView()
        # root.add_widget(tv)
        # full_view = scrollview.ScrollView().add_widget(tv)

        tv.size_hint = 1, None
        tv.bind(minimum_height = tv.setter('height'))
        populate_tree_view(tv)
        root = ScrollView(pos = (0, 0))
        root.add_widget(tv)
        # self.add_widget(root)
        return root

#
# class POSFMApp(App):
#
#     def build(self):
#         return POSFM()

if __name__ == '__main__':
    POSFM().run()
