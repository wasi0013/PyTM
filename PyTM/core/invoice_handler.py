from PyTM import settings
from PyTM.core import data_handler
from PyTM.commands.project import _get_duration_str
import datetime


def generate(invoice_number, invoice_texts, user, project, discount=0):
    title, logo, foot_note = (
        invoice_texts["title"],
        invoice_texts["logo"],
        invoice_texts["foot_note"],
    )
    tasks = project["tasks"]
    duration = 0
    sub_total = 0

    for task, t in tasks.items():
        if t["status"] != settings.ABORTED:
            task_duration = int(round(t["duration"]))
            duration += task_duration
            sub_total += float(t["duration"] / 360) * float(user["hourly_rate"])
    if discount == "":
        discount = 0
    else:
        discount = float(discount)
    total = sub_total - discount
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.15/dist/tailwind.min.css" rel="stylesheet">
</head>
<body class="font-sans bg-gray-100">
    <div class="container mx-auto py-8">
        <div class="bg-white rounded-lg shadow-lg p-8">
            <div class="flex justify-between">
                <div class="flex items-center">
                    <img src="{logo}" width=150 alt="{user["name"]}" class="h-12 mr-4" style="height:auto;">
                    <div>
                        <h1 class="text-2xl font-semibold">{user["name"]}</h1>
                        {f"<p>{user['address']}</p>"if user['address'] else ''}
                        {f"<p>{user['email']}</p>"if user['email'] else ''}
                        {f"<p>{user['phone']}</p>"if user['phone'] else ''}
                        {f"<p>{user['website']}</p>"if user['website'] else ''}
                        </div>
                </div>
                <div class="text-right">
                    <p class="text-sm">Invoice {invoice_number}</p>
                    <p class="text-sm">Date: {datetime.datetime.now().date()}</p>
                    <h2 class="font-semibold">Bill to</h2>
                    <p>{project['meta']['client_name']}</p>
                    {f"<p>{project['meta']['client_address']}</p>"if project['meta']['client_address'] else ''}
                    {f"<p>{project['meta']['client_email']}</p>"if project['meta']['client_email'] else ''}
                    {f"<p>{project['meta']['client_phone']}</p>"if project['meta']['client_phone'] else ''}
                    {f"<p>{project['meta']['client_website']}</p>"if project['meta']['client_website'] else ''}
                </div>
            </div>
            <div class="text-left mb-4">
                <h1 class="text-2xl font-semibold">Project: {project['meta']['title']}</h1>
                <p>Date: {datetime.datetime.fromisoformat(project['created_at']).date()}</p>
                <p>Duration: {_get_duration_str(duration)}</p>
            </div>
            <div class="mt-4">
                <table class="w-full border-collapse border border-gray-300">
                    <thead>
                        <tr>
                            <th class="p-2 border border-gray-300">Task</th>
                            <th class="p-2 border border-gray-300">Description</th>
                            <th class="p-2 border border-gray-300">Hours</th>
                            <th class="p-2 border border-gray-300">Hourly Rate</th>
                            <th class="p-2 border border-gray-300">Fee</th>
                        </tr>
                    </thead>
                    <tbody>

                        {"\n".join(f'''<tr>
                            <td class="p-2 border border-gray-300">{task.replace("_", " ").replace("-", " ").title()}</td>
                            <td class="p-2 border border-gray-300">{t.get('description', '-')}</td>
                            <td class="p-2 border border-gray-300">{float(t['duration']/360):,.02f}</td>
                            <td class="p-2 border border-gray-300">{float(user['hourly_rate']):,.02f}$</td>
                            <td class="p-2 border border-gray-300">{float(t['duration']/360) * float(user['hourly_rate']):,.02f}</td>
                        </tr>''' for task, t in tasks.items())}
                        
                    </tbody>
                </table>
            </div>
            <div class="mt-4">
                <div class="flex justify-end">
                    <div class="w-1/2">
                        <table class="w-full">
                            <tr>
                                <td class="py-1">Subtotal:</td>
                                <td class="text-right py-1">{sub_total:,.02f}$</td>
                            </tr>
                            <tr>
                                <td class="py-1">Discount:</td>
                                <td class="text-right py-1">{discount:,.02f}$</td>
                            </tr>
                            <tr>
                                <td class="py-1"><strong>Total:</strong></td>
                                <td class="text-right py-1">{total:,.02f}$</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="mt-4">
                <p class="text-left text-sm">{foot_note}</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
