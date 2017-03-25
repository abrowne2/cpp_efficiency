'''
Author: Adam Browne
Description: Tool which assists in compiling c++ code
TODO: Implement cmake into this process, so you can make it more customizable.

'''
import sublime, subprocess
import sublime_plugin


#paints errors to the view's buffer.
class painterrors(sublime_plugin.TextCommand):
	def run(self, edit, **errors):
		error = errors['error']		
		#offset calls subprocess.view.text_point, which returns the offset (location) of insertion.
		offset = self.view.text_point(((int(error[:error.find(":")])-1)+errors['factor']), 0)
		self.view.insert(edit, offset, "/*" + ' '.join(error.split()).strip() + "*/\n")

class efficiencyTool(sublime_plugin.EventListener):
	def on_post_save(self, view):
		file_path = view.file_name()
		compatible = self.canUse(file_path[file_path.rfind("."):])
		if compatible:
			self.autoCompile(file_path, view)
	
	'''
	* Compiles CPP, if there is errors, it paints them to the buffer where they appear.
	* Render AddressSanitizer and shows Results; TODO: implement test cases.
	'''
	def autoCompile(self, path, view):	
		wrkdir = path[:path.rfind("/")]; file_name = path[path.rfind("/")+1:]
		output_exec = file_name[:file_name.find(".")]
		try:
			o = subprocess.Popen(['g++','-o', output_exec,'-g','-Wall','-Werror','-fsanitize=address','-std=c++11',file_name], 
				stderr=subprocess.PIPE, stdout=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True, cwd=wrkdir)
			output, errs = o.communicate(timeout=15)
		except Exception as e:
			print("Encountered the following: " + type(e))
		while o.poll() is None:
			pass
		print(o.args)				
		if len(errs) is not 0:
			if errs.find("AddressSanitizer") is -1:
				errors = errs.split(file_name + ':')
				factor = 0
				if '' in errors: 
					errors.remove('')
				#compute the factor / offset and paint the errors to the buffer.
				for err in errors:
					view.run_command("painterrors", {'error': err, 'factor': factor})
					factor += 1
			else:
				#replace the <> with [] because html parsing is wack:
				sanitize = errs.replace("<","[").replace(">", "]").split('\n')
				view.show_popup(content=''.join(['<p style="margin:1">' + line + '</p>' for line in sanitize]), 
					max_width=950, max_height=500)
		else:
			'''
			To use the builtin test suite, the cpp file must have a main function which
			has the ability to take command line arguments.
			'''
			o = subprocess.Popen(['./'+output_exec], stderr=subprocess.PIPE, stdout=subprocess.PIPE, 
				stdin=subprocess.PIPE, universal_newlines=True, cwd=wrkdir)
			output, errs = o.communicate(timeout=15)			
			view.show_popup('<p><b>STDOUT</b>: </p>' + ''.join(['<p style="margin:0">' + line + '</p>' 
				for line in output.split('\n')]))

	#consider implementing LLDB and debugging the stacktrace.
	def autoDebug(self, view):
		pass

	def canUse(self, ext):
		return ext == '.cpp' or ext == '.hpp' or ext == '.cc' or ext == '.h'