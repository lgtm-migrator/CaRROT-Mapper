import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.authtoken.models import Token
from .views import DatasetListView, ScanReportListViewSet
from .models import Project, Dataset, ScanReport, VisibilityChoices


class TestDatasetListView(TestCase):
    def setUp(self):
        User = get_user_model()
        # Set up users
        self.user1 = User.objects.create(username="gandalf", password="iwjfijweifje")
        Token.objects.create(user=self.user1)
        self.user2 = User.objects.create(username="aragorn", password="ooieriofiejr")
        Token.objects.create(user=self.user2)

        # Set up datasets
        self.public_dataset1 = Dataset.objects.create(
            name="Places in Middle Earth", visibility="PUBLIC"
        )
        self.public_dataset2 = Dataset.objects.create(
            name="Places in Valinor", visibility="PUBLIC"
        )
        self.public_dataset3 = Dataset.objects.create(
            name="The Rings of Power", visibility="PUBLIC"
        )
        self.restricted_dataset = Dataset.objects.create(
            name="Fellowship Members", visibility="RESTRICTED"
        )
        self.restricted_dataset.viewers.add(self.user1)

        # Set up projects
        self.project1 = Project.objects.create(name="The Fellowship of the Ring")
        self.project1.members.add(self.user1, self.user2)
        self.project1.datasets.add(
            self.public_dataset1,
            self.public_dataset2,
            self.restricted_dataset,  # user2 can't see
        )
        self.project2 = Project.objects.create(name="The Two Towers")
        self.project2.members.add(self.user1)
        self.project2.datasets.add(self.restricted_dataset)
        self.project3 = Project.objects.create(name="The Return of the King")
        self.project3.datasets.add(self.public_dataset3)

        # Request factory for setting up requests
        self.factory = APIRequestFactory()

        # The view for the tests
        self.view = DatasetListView.as_view()

    def test_dataset_returns(self):
        # Make the request for Datasets
        request = self.factory.get(f"api/datasets/")
        # Add user1 to the request; this is not automatic
        request.user = self.user1
        # Authenticate the user1
        force_authenticate(
            request,
            user=self.user1,
            token=self.user1.auth_token,
        )
        # Get the response data
        response_data = self.view(request).data

        # Assert user1 can only public_dataset1, public_dataset2
        # and restricted_dataset
        for obj in response_data:
            self.assertIn(
                obj.get("id"),
                [
                    self.public_dataset1.id,
                    self.public_dataset2.id,
                    self.restricted_dataset.id,
                ],
            )

        # Assert user1 can't see public_dataset3
        for obj in response_data:
            self.assertNotEqual(obj.get("id"), self.public_dataset3.id)

        # Add user2 to the request; this is not automatic
        request.user = self.user2
        # Authenticate the user2
        force_authenticate(
            request,
            user=self.user2,
            token=self.user2.auth_token,
        )
        # Get the response
        response_data = self.view(request).data

        # Assert user2 can only public_dataset1 and public_dataset2
        for obj in response_data:
            self.assertIn(
                obj.get("id"),
                [self.public_dataset1.id, self.public_dataset2.id],
            )

        # Assert user2 can't see public_dataset3
        for obj in response_data:
            self.assertNotEqual(obj.get("id"), self.public_dataset3.id)

    def test_dataset_filtering(self):
        # Make the request for the public_dataset1
        request = self.factory.get(
            f"api/datasets/", {"id__in": self.public_dataset1.id}
        )
        # Add user1 to the request; this is not automatic
        request.user = self.user1
        # Authenticate user1
        force_authenticate(
            request,
            user=self.user1,
            token=self.user1.auth_token,
        )
        # Get the response
        response_data = self.view(request).data

        # Assert only got public_dataset1
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0].get("id"), self.public_dataset1.id)

        # Make the request for the public_dataset3
        request = self.factory.get(
            f"api/datasets/", {"id__in": self.public_dataset3.id}
        )
        # Add user1 to the request; this is not automatic
        request.user = self.user1
        # Authenticate user1
        force_authenticate(
            request,
            user=self.user1,
            token=self.user1.auth_token,
        )
        # Get the response
        response_data = self.view(request).data

        # Assert response is empty
        self.assertEqual(response_data, [])

    def test_az_function_user_perm(self):
        User = get_user_model()
        az_user = User.objects.get(username=os.getenv("AZ_FUNCTION_USER"))
        # Make the request for the Dataset
        request = self.factory.get(f"api/datasets/")
        # Add the user to the request; this is not automatic
        request.user = az_user
        # Authenticate az_user
        force_authenticate(
            request,
            user=az_user,
            token=az_user.auth_token,
        )
        # Get the response
        response_data = self.view(request).data
        # Assert az_user can see all datasets
        obj_ids = [obj.get("id") for obj in response_data]
        self.assertTrue(Dataset.objects.filter(id__in=obj_ids).exists())


class TestScanScanReportListViewset(TestCase):
    def setUp(self):
        User = get_user_model()
        # Set up users
        self.user1 = User.objects.create(username="gandalf", password="iwjfijweifje")
        Token.objects.create(user=self.user1)
        self.user2 = User.objects.create(username="aragorn", password="ooieriofiejr")
        Token.objects.create(user=self.user2)

        # Set up datasets
        self.public_dataset = Dataset.objects.create(
            name="Places in Middle Earth", visibility=VisibilityChoices.PUBLIC
        )
        self.restricted_dataset = Dataset.objects.create(
            name="Fellowship Members", visibility=VisibilityChoices.RESTRICTED
        )
        self.restricted_dataset.viewers.add(self.user1)

        # Set up scan reports
        self.public_scanreport = ScanReport.objects.create(
            dataset="The Mines of Moria",
            visibility=VisibilityChoices.PUBLIC,
            parent_dataset=self.public_dataset
        )
        self.restricted_scanreport1 = ScanReport.objects.create(
            dataset="The Rings of Power",
            visibility=VisibilityChoices.RESTRICTED,
            parent_dataset=self.public_dataset,
        )
        self.restricted_scanreport1.viewers.add(self.user1, self.user2)
        self.restricted_scanreport2 = ScanReport.objects.create(
            dataset="The Balrogs of Morgoth",
            visibility=VisibilityChoices.RESTRICTED,
            parent_dataset=self.restricted_dataset,
        )
        self.restricted_scanreport2.viewers.add(self.user1)

        # Set up projects
        self.project1 = Project.objects.create(name="The Fellowship of the Ring")
        self.project1.members.add(self.user1, self.user2)
        self.project1.datasets.add(
            self.public_dataset,
            self.restricted_dataset,
        )
        self.project2 = Project.objects.create(name="The Two Towers")
        self.project2.members.add(self.user1)
        self.project2.datasets.add(self.restricted_dataset)

        # Request factory for setting up requests
        self.factory = APIRequestFactory()

        # The view for the tests
        self.view = ScanReportListViewSet.as_view({"get": "list"})

    def test_scanreport_returns(self):
        # Make the request for Datasets
        request = self.factory.get(f"/scanreports/")
        # Add user1 to the request; this is not automatic
        request.user = self.user1
        # Authenticate the user1
        force_authenticate(
            request,
            user=self.user1,
            token=self.user1.auth_token,
        )
        # Get the response data
        response_data = self.view(request).data

        # Assert user1 can see all scan reports
        # and restricted_dataset
        for obj in response_data:
            self.assertIn(
                obj.get("id"),
                [
                    self.public_scanreport.id,
                    self.restricted_scanreport1.id,
                    self.restricted_scanreport2.id,
                ],
            )

        # Add user2 to the request; this is not automatic
        request.user = self.user2
        # Authenticate the user2
        force_authenticate(
            request,
            user=self.user2,
            token=self.user2.auth_token,
        )
        # Get the response
        response_data = self.view(request).data

        # Assert user2 can see public_scanreport and restricted_scanreport1
        for obj in response_data:
            self.assertIn(
                obj.get("id"),
                [self.public_scanreport.id, self.restricted_scanreport1.id],
            )

        # Assert user2 can't see restricted_scanreport2
        for obj in response_data:
            self.assertNotEqual(obj.get("id"), self.restricted_scanreport2.id)

    def test_az_function_user_perm(self):
        User = get_user_model()
        az_user = User.objects.get(username=os.getenv("AZ_FUNCTION_USER"))
        # Make the request for the Dataset
        request = self.factory.get(f"/scanreports/")
        # Add the user to the request; this is not automatic
        request.user = az_user
        # Authenticate az_user
        force_authenticate(
            request,
            user=az_user,
            token=az_user.auth_token,
        )
        # Get the response
        response_data = self.view(request).data
        # Assert az_user can see all scan reports
        obj_ids = [obj.get("id") for obj in response_data]
        self.assertTrue(ScanReport.objects.filter(id__in=obj_ids).exists())