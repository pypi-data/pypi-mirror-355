# Copyright 2023 Ross J. Duff MSc
# The copyright holder licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
project('blastpipe', version: '0.1.0')
fs               = import('fs')
author           = 'Ross J. Duff MSc'
copyright_date   = '2023'
html_theme       = get_option('html_theme')
copyright        = ', '.join([copyright_date, author])
sphinx           = find_program('sphinx-build')
exclude_patterns = ','.join(get_option('exclude_patterns'))
sphinx_ext       = ','.join(get_option('sphinx_ext'))
html_static_path = ','.join(get_option('html_static_path'))
templates_path   = ','.join(get_option('templates_path'))
configure_file(input: 'conf.cfg', output: 'conf.py' ,configuration: configuration_data({
 'author'          : author,
 'copyright'       : copyright,
 'html_theme'      : html_theme,
 'html_static_path': html_static_path,
 'templates_path'  : templates_path,
 'extensions'      : '[\n    "@0@"\n]'.format('",\n    "'.join(get_option('sphinx_ext'))),
 'project_name'    : meson.project_name(),
 'exclude_patterns': '["@0@"]'.format('", "'.join(get_option('exclude_patterns'))),
}))
pdflatex = find_program('pdflatex', disabler: true)
builder_dirs     = {'html': 'dirhtml', 'man': 'man'}
if pdflatex.found()
 builder_dirs += {'pdf': 'latex'}
endif
foreach dir: [html_static_path, templates_path]
 subdir(dir)
endforeach
all = ['index.rst']
foreach source: all
 fs.copyfile(source)
endforeach
env = environment()
env.append('PYTHONPATH', meson.global_build_root())
foreach name, builder: builder_dirs 
 sphinx_args = [sphinx, '-C',
  '-Dhtml_static_path='+ html_static_path,
  '-Dexclude_patterns='+ exclude_patterns,
  '-Dextensions='      + sphinx_ext,
  '-Dtemplates_path='  + templates_path,
  '-Dproject='         + meson.project_name(),
  '-Dauthor='          + author,
  '-Dcopyright='       + copyright,
  '-Dhtml_theme='      + html_theme,
  '-j', 'auto',
  '-W',
  '-E', 
  '-a',
  '-b', builder]
 sphinx_args += meson.project_build_root()
 sphinx_args += '@OUTPUT@'
 custom_target(name, command: sphinx_args, input: all, output: name, env: env, install: true,
  install_dir: get_option('datadir')/'doc', install_tag: 'doc'+name)
endforeach
