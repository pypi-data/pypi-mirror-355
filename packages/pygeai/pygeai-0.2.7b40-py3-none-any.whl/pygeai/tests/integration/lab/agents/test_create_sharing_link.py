from unittest import TestCase
import unittest
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import SharingLink
from pygeai.core.common.exceptions import MissingRequirementException

ai_lab_manager: AILabManager

class TestAILabCreateSharingLinkIntegration(TestCase):  

    def setUp(self):
        self.ai_lab_manager = AILabManager(alias="beta")
        self.project_id = "be4889df-cacc-4e6f-b3bb-153c4ac0d168"
        self.agent_id = "0026e53d-ea78-4cac-af9f-12650e5bb6d9" 

    def __create_sharing_link(self, agent_id=None, project_id=None):
        return self.ai_lab_manager.create_sharing_link(
            project_id=self.project_id if project_id is None else project_id,
            agent_id=self.agent_id if agent_id is None else agent_id
        )
    

    def test_create_sharing_link(self):    
        shared_link = self.__create_sharing_link()        
        self.assertIsInstance(shared_link, SharingLink, "Expected response to be an instance of SharingLink")
       
        self.assertEqual(
            shared_link.agent_id,
            self.agent_id,
            "Returned agentId should match the requested agent_id"
        )
        self.assertTrue(
            shared_link.api_token.startswith("shared-"),
            "apiToken should start with 'shared-'"
        )
        self.assertTrue(
            shared_link.shared_link.startswith("https://"),
            "sharedLink should be a valid URL"
        )
        self.assertIn(
            f"agentId={self.agent_id}",
            shared_link.shared_link,
            "sharedLink should contain the agentId as a query parameter"
        )
        self.assertIn(
            f"sharedToken={shared_link.api_token}",
            shared_link.shared_link,
            "sharedLink should contain the apiToken as sharedToken"
        )


    def test_create_sharing_link_no_project(self):
        with self.assertRaises(MissingRequirementException) as context:
            self.__create_sharing_link(project_id="")
        self.assertEqual(
            str(context.exception),
            "Cannot create sharing link without specifying project_id",
            "Expected exception for missing project_id"
        )


    def test_create_sharing_link_no_agent_id(self):
        with self.assertRaises(MissingRequirementException) as context:
            self.__create_sharing_link(agent_id="")
        self.assertEqual(
            str(context.exception),
            "agent_id must be specified in order to create sharing link",
            "Expected exception for missing agent_id"
        )

    @unittest.skip("A descriptive error exception is expected")
    def test_create_sharing_link_invalid_agent_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        shared_link = self.__create_sharing_link(agent_id=invalid_id)

        """ self.assertEqual(
            deleted_agent.content["messages"][0]["description"],
            f"Agent not found [IdOrName= {invalid_id}].",
            "Expected error message for invalid agent id"
        ) """


    def test_create_sharing_link_invalid_project_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        shared_link = self.__create_sharing_link(project_id=invalid_id)

        self.assertIsInstance(shared_link, SharingLink, "Expected response to be an instance of SharingLink")
       
        self.assertEqual(
            shared_link.agent_id,
            self.agent_id,
            "Returned agentId should match the requested agent_id"
        )
        self.assertTrue(
            shared_link.api_token.startswith("shared-"),
            "apiToken should start with 'shared-'"
        )
        self.assertTrue(
            shared_link.shared_link.startswith("https://"),
            "sharedLink should be a valid URL"
        )