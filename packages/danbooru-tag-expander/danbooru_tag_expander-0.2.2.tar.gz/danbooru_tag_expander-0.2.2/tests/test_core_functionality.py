"""Tests for core TagExpander functionality with graph cache."""

import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from collections import Counter
from danbooru_tag_expander import TagExpander


class TestTagExpanderCore(unittest.TestCase):
    """Test cases for the core TagExpander functionality."""

    def setUp(self):
        """Set up the test case."""
        # Create a temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock client
        self.mock_client = MagicMock()
        
        # Create a TagExpander with the mock client and cache enabled
        with patch('danbooru_tag_expander.utils.tag_expander.Danbooru', return_value=self.mock_client):
            self.expander = TagExpander(
                username="test", 
                api_key="test", 
                use_cache=True,
                cache_dir=self.temp_dir
            )

    def tearDown(self):
        """Clean up after test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_expand_tags_basic_functionality(self):
        """Test basic tag expansion functionality."""
        # Mock API responses for tag data
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                tag_name = params["search[name]"]
                # Mock deprecated status (all non-deprecated for simplicity)
                return [{"name": tag_name, "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                tag_name = params.get("search[antecedent_name]")
                # Mock some simple implications
                if tag_name == "kitten":
                    return [{"antecedent_name": "kitten", "consequent_name": "cat", "status": "active"}]
                elif tag_name == "cat":
                    return [{"antecedent_name": "cat", "consequent_name": "animal", "status": "active"}]
                elif tag_name == "animal":
                    return []  # animal has no further implications
                return []
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                # Mock aliases (none for simplicity)
                return [{"name": params["search[name_matches]"], "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # Test expanding tags with implications
        expanded_tags, frequencies = self.expander.expand_tags(["kitten"])
        
        # Should include the original tag plus its transitive implications
        expected_tags = {"kitten", "cat", "animal"}
        self.assertEqual(expanded_tags, expected_tags)
        
        # Check frequencies: kitten=1, cat=1 (from kitten), animal=1 (from cat)
        self.assertEqual(frequencies["kitten"], 1)
        self.assertEqual(frequencies["cat"], 1)
        self.assertEqual(frequencies["animal"], 1)

    def test_expand_tags_with_aliases(self):
        """Test tag expansion with aliases."""
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                tag_name = params["search[name]"]
                return [{"name": tag_name, "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                return []  # No implications for simplicity
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                tag_name = params["search[name_matches]"]
                if tag_name == "cat":
                    return [{
                        "name": "cat",
                        "consequent_aliases": [
                            {"antecedent_name": "feline", "status": "active"}
                        ]
                    }]
                return [{"name": tag_name, "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # Test expanding tags with aliases
        expanded_tags, frequencies = self.expander.expand_tags(["cat"])
        
        # Should include both the original tag and its alias
        expected_tags = {"cat", "feline"}
        self.assertEqual(expanded_tags, expected_tags)
        
        # Aliases should share the same frequency
        self.assertEqual(frequencies["cat"], 1)
        self.assertEqual(frequencies["feline"], 1)

    def test_expand_tags_multiple_input(self):
        """Test expanding multiple input tags."""
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                tag_name = params["search[name]"]
                return [{"name": tag_name, "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                tag_name = params.get("search[antecedent_name]")
                if tag_name in ["tag1", "tag2"]:
                    return [{"antecedent_name": tag_name, "consequent_name": "common", "status": "active"}]
                return []
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                return [{"name": params["search[name_matches]"], "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # Test expanding multiple tags that imply the same tag
        expanded_tags, frequencies = self.expander.expand_tags(["tag1", "tag2"])
        
        # Should include original tags and their common implication
        expected_tags = {"tag1", "tag2", "common"}
        self.assertEqual(expanded_tags, expected_tags)
        
        # The common tag should have frequency 2 (from both inputs)
        self.assertEqual(frequencies["tag1"], 1)
        self.assertEqual(frequencies["tag2"], 1)
        self.assertEqual(frequencies["common"], 2)

    def test_expand_tags_no_cache_raises_error(self):
        """Test that expand_tags raises error when cache is disabled."""
        # Create expander without cache
        with patch('danbooru_tag_expander.utils.tag_expander.Danbooru', return_value=self.mock_client):
            expander_no_cache = TagExpander(
                username="test", 
                api_key="test", 
                use_cache=False
            )
        
        # Should raise RuntimeError
        with self.assertRaises(RuntimeError) as context:
            expander_no_cache.expand_tags(["test"])
        
        self.assertIn("Graph cache is not enabled", str(context.exception))

    def test_external_tag_graph_injection(self):
        """Test that external DanbooruTagGraph can be injected."""
        from danbooru_tag_graph import DanbooruTagGraph
        
        # Create external graph with pre-populated data
        external_graph = DanbooruTagGraph()
        external_graph.add_tag("dog", fetched=True)
        external_graph.add_tag("animal", fetched=True)
        external_graph.add_implication("dog", "animal")
        
        # Create expander with external graph
        with patch('danbooru_tag_expander.utils.tag_expander.Danbooru', return_value=self.mock_client):
            expander = TagExpander(
                username="test",
                api_key="test",
                tag_graph=external_graph
            )
        
        # Should use the pre-populated graph without API calls
        expanded_tags, frequencies = expander.expand_tags(["dog"])
        
        # Should include both tags from the pre-populated graph
        expected_tags = {"dog", "animal"}
        self.assertEqual(expanded_tags, expected_tags)
        
        # Check frequencies
        self.assertEqual(frequencies["dog"], 1)
        self.assertEqual(frequencies["animal"], 1)
        
        # Verify no API calls were made since data was pre-populated
        self.mock_client._get.assert_not_called()

    def test_get_implications_direct(self):
        """Test getting direct implications from cached graph data."""
        # Set up mock API responses to populate cache
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                return [{"name": params["search[name]"], "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                tag_name = params.get("search[antecedent_name]")
                if tag_name == "kitten":
                    return [{"antecedent_name": "kitten", "consequent_name": "cat", "status": "active"}]
                return []
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                return [{"name": params["search[name_matches]"], "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # First populate the cache
        self.expander.expand_tags(["kitten"])
        
        # Now test direct implications method
        implications = self.expander.get_implications("kitten")
        self.assertEqual(implications, ["cat"])
        
        # Test non-existent tag
        implications = self.expander.get_implications("nonexistent")
        self.assertEqual(implications, [])

    def test_get_transitive_implications(self):
        """Test getting transitive implications from cached graph data."""
        # Set up mock API responses for transitive chain: kitten -> cat -> animal
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                return [{"name": params["search[name]"], "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                tag_name = params.get("search[antecedent_name]")
                if tag_name == "kitten":
                    return [{"antecedent_name": "kitten", "consequent_name": "cat", "status": "active"}]
                elif tag_name == "cat":
                    return [{"antecedent_name": "cat", "consequent_name": "animal", "status": "active"}]
                return []
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                return [{"name": params["search[name_matches]"], "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # First populate the cache
        self.expander.expand_tags(["kitten"])
        
        # Now test transitive implications method
        transitive_implications = self.expander.get_transitive_implications("kitten")
        expected = {"cat", "animal"}
        self.assertEqual(transitive_implications, expected)
        
        # Test direct implications vs transitive
        direct_implications = self.expander.get_implications("kitten")
        self.assertEqual(direct_implications, ["cat"])
        self.assertIn("animal", transitive_implications)
        self.assertNotIn("animal", direct_implications)

    def test_get_aliases_and_alias_group(self):
        """Test getting aliases and alias groups from cached graph data."""
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                return [{"name": params["search[name]"], "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                return []  # No implications for simplicity
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                tag_name = params["search[name_matches]"]
                if tag_name == "cat":
                    return [{
                        "name": "cat",
                        "consequent_aliases": [
                            {"antecedent_name": "feline", "status": "active"}
                        ]
                    }]
                elif tag_name == "feline":
                    return [{
                        "name": "feline", 
                        "consequent_aliases": [
                            {"antecedent_name": "kitty", "status": "active"}
                        ]
                    }]
                return [{"name": tag_name, "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # First populate the cache
        self.expander.expand_tags(["cat"])
        
        # Test direct aliases
        aliases = self.expander.get_aliases("cat")
        self.assertEqual(aliases, ["feline"])
        
        # Test alias group (should include all transitively connected aliases)
        alias_group = self.expander.get_alias_group("cat")
        # The alias group should include cat itself and all its transitive aliases
        self.assertIn("cat", alias_group)
        self.assertIn("feline", alias_group)

    def test_get_semantic_relations_comprehensive(self):
        """Test the comprehensive semantic relations method."""
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                return [{"name": params["search[name]"], "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                tag_name = params.get("search[antecedent_name]")
                if tag_name == "kitten":
                    return [{"antecedent_name": "kitten", "consequent_name": "cat", "status": "active"}]
                elif tag_name == "cat":
                    return [{"antecedent_name": "cat", "consequent_name": "animal", "status": "active"}]
                return []
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                tag_name = params["search[name_matches]"]
                if tag_name == "kitten":
                    return [{
                        "name": "kitten",
                        "consequent_aliases": [
                            {"antecedent_name": "baby_cat", "status": "active"}
                        ]
                    }]
                return [{"name": tag_name, "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # First populate the cache
        self.expander.expand_tags(["kitten"])
        
        # Test comprehensive semantic relations
        relations = self.expander.get_semantic_relations("kitten")
        
        # Check structure
        expected_keys = {'direct_implications', 'transitive_implications', 
                        'direct_aliases', 'alias_group', 'all_related'}
        self.assertEqual(set(relations.keys()), expected_keys)
        
        # Check content
        self.assertEqual(relations['direct_implications'], ["cat"])
        self.assertEqual(relations['transitive_implications'], {"cat", "animal"})
        self.assertEqual(relations['direct_aliases'], ["baby_cat"])
        self.assertIn("kitten", relations['alias_group'])
        self.assertIn("baby_cat", relations['alias_group'])
        
        # all_related should contain transitive implications and alias group (minus original tag)
        expected_related = {"cat", "animal", "baby_cat"}
        self.assertEqual(relations['all_related'], expected_related)

    def test_is_tag_cached(self):
        """Test checking if a tag is cached."""
        def mock_api_request(endpoint, params):
            if endpoint == "tags.json" and "search[name]" in params:
                return [{"name": params["search[name]"], "is_deprecated": False}]
            elif endpoint == "tag_implications.json":
                return []
            elif endpoint == "tags.json" and "search[name_matches]" in params:
                return [{"name": params["search[name_matches]"], "consequent_aliases": []}]
            return []
        
        self.mock_client._get.side_effect = mock_api_request
        
        # Initially, tag should not be cached
        self.assertFalse(self.expander.is_tag_cached("test_tag"))
        
        # After expanding, tag should be cached
        self.expander.expand_tags(["test_tag"])
        self.assertTrue(self.expander.is_tag_cached("test_tag"))

    def test_semantic_methods_without_cache_raise_error(self):
        """Test that semantic relationship methods raise error when cache is disabled."""
        # Create expander without cache
        with patch('danbooru_tag_expander.utils.tag_expander.Danbooru', return_value=self.mock_client):
            expander_no_cache = TagExpander(
                username="test", 
                api_key="test", 
                use_cache=False
            )
        
        # All semantic methods should raise RuntimeError
        methods_to_test = [
            ('get_implications', ["test"]),
            ('get_transitive_implications', ["test"]),
            ('get_aliases', ["test"]),
            ('get_alias_group', ["test"]),
            ('get_semantic_relations', ["test"]),
            ('is_tag_cached', ["test"])
        ]
        
        for method_name, args in methods_to_test:
            with self.subTest(method=method_name):
                method = getattr(expander_no_cache, method_name)
                with self.assertRaises(RuntimeError) as context:
                    method(*args)
                self.assertIn("Graph cache is not enabled", str(context.exception))


if __name__ == '__main__':
    unittest.main() 