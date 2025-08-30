if __name__ == '__main__':
    import os
    from config import config
    from ok import OK

    # Extend tasks with plugins without modifying upstream config.py
    config = config
    config.setdefault('onetime_tasks', [])
    # Avoid duplicate injection when re-running in same session
    plugin_entry = ["plugins.echo_merge.EchoMergeTask", "EchoMergeTask"]
    if plugin_entry not in config['onetime_tasks']:
        config['onetime_tasks'].append(plugin_entry)

    # Debug/logs: enable via env for packaging parity
    if os.environ.get('OK_DEBUG', '').lower() in ('1', 'true', 'yes'):
        config['debug'] = True
    os.makedirs('logs', exist_ok=True)

    # Scheme A: allow overriding update source to your fork via env
    # Set OK_PLUGINS_UPDATE_URL to your forked ok-ww-update repo to preserve plugins across updates
    update_url = os.environ.get('OK_PLUGINS_UPDATE_URL')
    pip_url = os.environ.get('OK_PLUGINS_PIP_URL', 'https://pypi.org/simple/')
    if update_url:
        git_update = config.get('git_update') or {}
        sources = list((git_update.get('sources') or []))
        # Prepend custom source
        sources.insert(0, {
            'name': 'Plugins',
            'git_url': update_url,
            'pip_url': pip_url
        })
        git_update['sources'] = sources
        config['git_update'] = git_update

    ok = OK(config)
    ok.start()
