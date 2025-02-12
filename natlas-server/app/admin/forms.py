from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, PasswordField, IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, Optional
from app.models import User, ScopeItem, AgentScript
import ipaddress
from app.elastic import Elastic

class ConfigForm(FlaskForm):
	login_required = BooleanField('Login Required')
	register_allowed = BooleanField('Registration Allowed')
	agent_authentication = BooleanField('Agent Authentication Required')
	elasticsearch_url = StringField("Elastic URL")
	mail_from = StringField("From Address", validators=[Email(), Optional()])
	mail_server = StringField("Mail Server")
	mail_port = StringField("Mail Port")
	mail_use_tls = BooleanField("Use TLS")
	mail_username = StringField("Mail username")
	mail_password = PasswordField("Mail password")
	submit = SubmitField("Save Changes")

	def validate_elasticsearch_url(self, elasticsearch_url):
		tmpElasticInstance = Elastic(elasticsearch_url.data)
		if not tmpElasticInstance.status:
			raise ValidationError("%s : %s" % (tmpElasticInstance.errorinfo, elasticsearch_url.data))

class InviteUserForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Invite User')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('Email %s already exists!' % user.email)


class UserDeleteForm(FlaskForm):
	deleteUser = SubmitField('Delete User')


class UserEditForm(FlaskForm):
	editUser = SubmitField('Toggle Admin')


class NewScopeForm(FlaskForm):
	target = StringField('Target', validators=[DataRequired()])
	blacklist = BooleanField('Blacklist')
	submit = SubmitField('Add Target')

	def validate_target(self, target):
		if '/' not in target.data:
			target.data = target.data + '/32'
		try:
			isValid = ipaddress.ip_network(target.data, False)
			item = ScopeItem.query.filter_by(target=isValid.with_prefixlen).first()
			if item is not None:
				raise ValidationError('Target %s already exists!' % item.target)
		except ipaddress.AddressValueError:
			raise ValidationError(
				'Target %s couldn\'t be validated' % target.data)

class ImportScopeForm(FlaskForm):
	scope = TextAreaField("Scope Import")
	submit = SubmitField("Import Scope")

class ImportBlacklistForm(FlaskForm):
	scope = TextAreaField("Blacklist Import")
	submit = SubmitField("Import Blacklist")

class ScopeDeleteForm(FlaskForm):
	deleteScopeItem = SubmitField('Delete Target')


class ScopeToggleForm(FlaskForm):
	toggleScopeItem = SubmitField('Toggle Blacklist')


class ServicesUploadForm(FlaskForm):
	serviceFile = FileField('Select a file to upload')
	uploadFile = SubmitField('Upload Services File')

class AddServiceForm(FlaskForm):
	serviceName = StringField('Service Name', validators=[DataRequired()])
	servicePort = IntegerField('Service Port', validators=[DataRequired()])
	serviceProtocol = SelectField("Protocol", validators=[DataRequired()])
	addService = SubmitField('Add Service')

	def validate_serviceName(self, serviceName):
		if ' ' in serviceName.data:
			raise ValidationError('Service names cannot contain spaces! Use - instead.')

	def validate_servicePort(self, servicePort):
		if servicePort.data > 65535 or servicePort.data < 0:
			raise ValidationError('Port has to be withing range of 0-65535')

class AgentConfigForm(FlaskForm):
	versionDetection = BooleanField("Version Detection (-sV)")
	osDetection = BooleanField("OS Detection (-O)")
	enableScripts = BooleanField("Scripting Engine (--script)")
	onlyOpens = BooleanField("Open Ports Only (--open)")
	scanTimeout = IntegerField("Maximum Nmap Run Time")
	webScreenshots = BooleanField("Web Screenshots (aquatone)")
	vncScreenshots = BooleanField("VNC Screenshots (vncsnapshot)")
	scriptTimeout = IntegerField("Script Timeout (--script-timeout)")
	hostTimeout = IntegerField("Host Timeout (--host-timeout)")
	osScanLimit = BooleanField("Limit OS Scan (--osscan-limit)")
	noPing = BooleanField("No Ping (-Pn)")

	updateAgents = SubmitField("Update Agent Config")

class AddScriptForm(FlaskForm):
	scriptName = StringField("Script Name", validators=[DataRequired()])
	addScript = SubmitField("Add Script")

	def validate_scriptname(self, scriptName):
		script = AgentScript.query.filter_by(name=scriptName).first()
		if script is not None:
			raise ValidationError('%s already exists!' % script.name)

class DeleteForm(FlaskForm):
	delete = SubmitField("Delete")

class AddTagForm(FlaskForm):
	tagname = StringField("Tag Name", validators=[DataRequired()])
	addTag = SubmitField("Add Tag")

class TagScopeForm(FlaskForm):
	tagname = SelectField("Tag Name", validators=[DataRequired()])
	addTagToScope = SubmitField("Add Tag to Scope")