def replace_in_file(filepath, old_str, new_str):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content.replace(old_str, new_str)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

replace_in_file('components/IncidentsPanel.js', 'focus:border-cyan-400', 'focus:border-neutral-400')
replace_in_file('components/IncidentsPanel.js', 'focus:ring-cyan-400/15', 'focus:ring-neutral-400/15')
replace_in_file('components/IncidentsPanel.js', 'text-white0', 'text-neutral-500')
replace_in_file('components/Sidebar.js', 'text-white0', 'text-neutral-500')
replace_in_file('components/Sidebar.js', 'bg-slate-800', 'bg-neutral-900')
replace_in_file('components/Sidebar.js', 'group-hover:text-slate-200', 'group-hover:text-white')

