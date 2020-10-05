import json
import os.path
from pathlib import Path

from googletrans import Translator
from core.base.model.AliceSkill import AliceSkill
from core.dialog.model.DialogSession import DialogSession
from core.util.Decorators import IntentHandler


class SkillTranslator(AliceSkill):
	"""
	Author: LazzaAU
	Description: Translate your skill into other languages
	"""


	def __init__(self):

		self._translatedData = dict()
		self._supportedLanguages = ['en', 'de', 'it', 'fr']
		self._skillLanguage = ""
		self._skillName = ""
		self._translationPath = Path
		self._manualPath = Path
		super().__init__()


	@IntentHandler('TranslateSkill')
	def translateSkill(self, session: DialogSession, **_kwargs):
		if not self.getConfig('skillLang') or not self.getConfig('skillLang') in self._supportedLanguages:
			self.logWarning(f'Skill Language in settings is not valid')
			return

		# get the default language of the skill from config
		self._skillLanguage = self.getConfig('skillLang')
		# list of supported languages
		self._supportedLanguages.remove(self._skillLanguage)

		if not self.getConfig('skillTitle'):
			self._skillName = self.name
		else:
			self._skillName = self.getConfig('skillTitle')

		# Set the path of the skill folder to translate
		if self.getConfig('skillPath'):
			self._translationPath = Path(f'{self.getConfig("skillPath")}/{self._skillName}')
		else:
			self._translationPath = Path(self.Commons.rootDir(), f'skills/{self._skillName}')

		if self.getConfig('skillTitle') and not self._translationPath.exists():
			self.logWarning(f'Can\'t find {self._skillName}. Please check your spelling')
			return

		# triggers the main code process
		self.iterateActiveLanguage()

		self.endDialog(
			sessionId=session.sessionId,
			text=self.randomTalk(text='startTranslate'),
			siteId=session.siteId
		)


	def iterateActiveLanguage(self):
		self.logInfo(f'Translating {self._skillName} skill....')
		for activeLanguage in self._supportedLanguages:
			self.translateTalksfile(activeLanguage)
			self.translateDialogFile(activeLanguage)
			self.translateSynonyms(activeLanguage)
		self.writeInstallConditions()
		self.logInfo(f'Completed Translation of the {self._skillName} skill. Please restart Alice')


	def translateTalksfile(self, activeLanguage):
		self.logDebug(f'Translating Talks file in {activeLanguage}')
		# Path to the active language talks file
		file = Path(f'{self._translationPath}/talks/{self._skillLanguage}.json')

		# load the contents of the active language file
		talksData = json.loads(file.read_text())
		# create instance of translator
		translator = Translator()

		# Check if we have all the language files. If not make them
		if not os.path.isfile(Path(f'{self._translationPath}/talks/{activeLanguage}.json')):
			with open(Path(f'{self._translationPath}/talks/{activeLanguage}.json'), 'x'):
				self.logInfo(f'File {activeLanguage}.json did not exist. So I created it')

		# choose the file to be translated
		translatedFile = Path(f'{self._translationPath}/talks/{activeLanguage}.json')
		for key, value in talksData.items():
			defaultList = list()
			shortList = list()

			for i, defaultTalk in enumerate(value['default']):

				translated = translator.translate(defaultTalk, dest=activeLanguage)
				defaultList.append(translated.text)

			for i, shortTalk in enumerate(value['short']):
				translated = translator.translate(shortTalk, dest=activeLanguage)
				shortList.append(translated.text)

			if defaultList[0] and shortList[0]:

				temp = {
					'default': defaultList,
					'short'  : shortList
				}
			else:
				temp = {
					'default': defaultList
				}

			self._translatedData[f'{key}'] = temp

		translatedFile.write_text(json.dumps(self._translatedData, ensure_ascii=False, indent=4))


	def translateDialogFile(self, activeLanguage):
		self.logDebug(f'Translating utterances in dialogTemplate file in {activeLanguage}')
		# Check for the language file. if not then create them
		if not os.path.isfile(Path(f'{self._translationPath}/dialogTemplate/{activeLanguage}.json')):
			with open(Path(f'{self._translationPath}/dialogTemplate/{activeLanguage}.json'), 'x'):
				self.logInfo(f'Dialog file {activeLanguage}.json did not exist. So I created it')

		# The Language file that the skill was written in
		file = Path(f'{self._translationPath}/dialogTemplate/{self._skillLanguage}.json')
		# The file we are going to translate into
		translatedFile = Path(f'{self._translationPath}/dialogTemplate/{activeLanguage}.json')

		dialogData = json.loads(file.read_text())
		translator = Translator()

		for i, item in enumerate(dialogData['intents']):

			dialogList = list()
			for utterance in item['utterances']:
				translated = translator.translate(utterance, dest=activeLanguage)
				dialogList.append(translated.text)

			item['utterances'] = dialogList

		translatedFile.write_text(json.dumps(dialogData, ensure_ascii=False, indent=4))


	def translateSynonyms(self, activeLanguage):
		self.logDebug(f'Translating synonyms in {activeLanguage}')
		# The Language file the skill was written in
		file = Path(f'{self._translationPath}/dialogTemplate/{self._skillLanguage}.json')
		# The language dile we are going to translate into
		translatedFile = Path(f'{self._translationPath}/dialogTemplate/{activeLanguage}.json')

		synonymData = json.loads(file.read_text())
		translator = Translator()

		for i, item in enumerate(synonymData['slotTypes']):

			synList = list()
			for slotValue in item['values']:
				# Using try in case user has empty Synonym lists (index out of range errors)
				try:
					for synonym in slotValue['synonyms']:
						translated = translator.translate(synonym, dest=activeLanguage)
						synList.append(translated.text)
						synList.append(synonym)
						print(f' synlist is {synList}')
					item['values'][0]['synonyms'] = synList
				except:
					continue
				translatedFile.write_text(json.dumps(synonymData, ensure_ascii=False, indent=4))


	def writeInstallConditions(self):
		self.logDebug(f'Updating the install file')
		# Lets update the install file language conditions
		file = Path(f'{self._translationPath}/{self._skillName}.install')
		installData = json.loads(file.read_text())
		supportedLanguages = ['en', 'de', 'it', 'fr']

		for i, item in enumerate(installData['conditions']):
			if 'lang' in item:
				installData['conditions']['lang'] = supportedLanguages
				file.write_text(json.dumps(installData, ensure_ascii=False, indent=4))
