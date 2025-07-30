import * as JsSearch from 'js-search';
import { returnedMaterial } from '../../models/typedefs';

/*
	This does a full text match on all of incoming snippets
	it is intended to be used when our search space is not the user's entire PFD database.
*/
export const doSearch = ({
  query,
  snippets,
}: {
  query: string;
  snippets: returnedMaterial[];
}) => {
  const search = new JsSearch.Search('id');
  search.addIndex('language');
  search.addIndex('raw');
  search.addIndex('title');
  search.addIndex('description');
  search.addDocuments(snippets);
  return search.search(query) as returnedMaterial[];
};
