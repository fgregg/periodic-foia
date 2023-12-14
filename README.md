# Periodic FOIA
Project to make periodic FOIA requests through MuckRock.

## Author request templates
FOIA requests templates are markdown files, that look like this.

```markdown
---
agency: 3036
title: Count of City Keys Issued in {previous_month}
muckrock_organization: the-foia-bakery
start_date: 2024-01-01
---

Records sufficient to show the number of CityKeys issued from {previous_month_start} to {previous_month_end}.
```

The bits at the top between the `---` lines are frontmatter, followed by the body. Muckrock will wrap the body in its location specific FOIA boilerplate.

In the body and the title, the bits between curly braces will be replaced by appropriate values. Right now we support seven of these variables:

* `{previous_month}`: The previous month styled like "October, 2023"
* `{previous_month_start}`: The first day of the previous month styled like "October 1, 2023"
* `{previous_month_end}`: The last day of the previous month styled like "October 30, 2023"
* `{previous_quarter}`: The previous quarter styled like "Quarter 3, 2023"
* `{previous_quarter_start}`: The first day of the previous quarter styled like "July 1, 2023"
* `{previous_quarter_end}`: The last of the previous quarter styled like "September 30, 2023"
* `{previous_year}`: The previous year

In the frontmatter, you need to set four pieces of information.

1. `agency`: Muckrock's agency number. You can get this from from the end of Muckrock's url for the agency. For example, the web page for the City Clerk of Chicago is https://www.muckrock.com/agency/chicago-169/office-of-the-city-clerk-3036/, and 3036 is the agency number.
2. `title`: The subject line of the request.
3. `muckrock_organization`: The slug of the organization you want the request to be associated with. You can get it from the url of your organization. For example, the organization with the url of https://www.muckrock.com/organization/the-foia-bakery/ has the slug `the-foia-bakery`.
4. `start_date`: Don't send the request until it's on or after this date.

See the some of [my request templates for examples](https://github.com/fgregg/periodic-foia/tree/main/forest_requests).

## Request Scheduling
On the first day of every month, we'll try to send an requests for all the request templates. Before we submit a request, we check to make sure that there is no request that has already been made to the same agency with the same title and body. If there is, then we do not submit, so we don't worry about duplication.

## Dry Run
To see what would be sent, without sending a request, you can run the Dry Run github action by clicking the "Run workflow" button on [the action's page](https://github.com/fgregg/periodic-foia/actions/workflows/dry_run.yaml). 
