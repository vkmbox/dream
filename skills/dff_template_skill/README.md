# dff_template_skill

## Description

**dff_template_skill** currently includes refactoring for  ** dummy_skill_dialog ** skill.

## Quickstart from docker

```bash
# create local.yml
python utils/create_local_yml.py -d assistant_dists/dream/ -s dff-template-skill
# build service
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml up -d --build dff-template-skill
# run tests
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml exec dff-template-skill bash test.sh
# check logs
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml logs -f dff-template-skill
# run a dialog with the agent
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/local.yml exec agent python -m deeppavlov_agent.run
```

## Quickstart without docker

```bash
pip install -r requirements.txt
gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}
```

## Resources

* Execution time: 46 ms
* Starting time: 1.5 sec
* RAM: 45 MB