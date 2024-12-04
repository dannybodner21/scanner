Attendees: Karun, Mark, Andrew, Veronika

Recapped work from last working session.  We worked as a group on Wednesday, and we're not sure what to document in terms of individual efforts

Sprint burndown chart so far:
![Burndown](images/Burndown_Nov10.png)

Impediments:
* Some issues with technology / meeting links (thankfully resolved)
* Reminder: Next sprint starts 11/18.  Stakeholder meeting scheduled for 11/17
* Reminder: Forecast may be incorrect (we had limited data to predict velocity)
* Using dynamic forms [seems possible but hard](https://stackoverflow.com/a/6142749) - let's stick with what we've got for now
* Is having the ability to do smaller meetings helpful?  E.g. having pairs working outside the Wednesday/Sunday
  * We'll continue as-is for today and the following Wednesday, but may meet again between Wednesday and next Sunday to meet assignment requirements (not add features)
* Review of rubric

Done:
* Added unit testing framework (using Django tools).  Notably this allows us to unit test database operations *without an external database*
* Added HTML formatting for ingredients (as an unordered list) as part of the Recipe model

TODO:
* Build additional tests
* Format recipe process steps as ordered list
* Develop a basic browse recipe page
* Prepare for stakeholder meeting
* Change redirect after adding a recipe to point to the recipe just added (currently it cheats and always points to the same recipe)
* Add minimal formatting to recipe view page, including unit tests (e.g. ingredients as unordered list, steps as ordered lists)
* Add syntax hinting to add recipe form (Process steps)