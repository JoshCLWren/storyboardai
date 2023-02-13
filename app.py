import asyncio

import aiohttp
import aiohttp_jinja2
import jinja2

import stable_diffusers

app = aiohttp.web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))


async def view_project(request):
    """
    View a project.
    :param request: the request object
    :return: the rendered html page
    """
    project_id = request.match_info["project_id"]
    project = stable_diff_2.Project(project_id)
    project.load()
    # render an html page with the project data
    await project.html_render()

    # return the rendered html page
    return aiohttp_jinja2.render_template(
        f"templates/projects/{project.id}.html", request, {"project": project}
    )


if __name__ == "__main__":
    app.router.add_get("/project/{project_id}", view_project)
    aiohttp.web.run_app(app)
