## Run Agent

**Run all scripts from the top level of the repo**

```
# process one file

{% if cookiecutter.data_type == 'text' -%}
cat inputs/test.txt | hl agent start agents/{{cookiecutter.agent_name}}.json
{% elif cookiecutter.data_type == 'video' -%}
hl agent start agents/{{cookiecutter.agent_name}}.json -f inputs/test.mp4
{% elif cookiecutter.data_type == 'image' -%}
hl agent start agents/{{cookiecutter.agent_name}}.json -f inputs/test.png
{%- endif %}
```
