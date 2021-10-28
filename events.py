import typing
if typing.TYPE_CHECKING:  # avoid circular imports
    from core import Environment, Service


def arrival(env: 'Environment', service: 'Service'):
    # logging.debug('Processing arrival {} for policy {} load {} seed {}'
    #               .format(service.service_id, env.policy, env.load, env.seed))

    success, dc, path = env.policy.route(service)

    if success:
        service.route = path
        env.provision_service(service)
    else:
        env.reject_service(service)

    env.setup_next_arrival()  # schedules next arrival


def departure(env: 'Environment', service: 'Service'):
    env.release_path(service)
