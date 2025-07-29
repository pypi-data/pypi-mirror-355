"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { PlusCircle, Search, Trash2, Users } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import axios from "axios";
import applyCaseMiddleware from "axios-case-converter";
import {getToken} from "@/lib/auth";

interface Group {
  groupId: string
  description: string
  members: string[] // User IDs
}

interface User {
  id: string
  name: string
  email: string
  role: string
}

export default function GroupManagement() {
  const [groups, setGroups] = useState<Group[]>([])
  const [users, setUsers] = useState<User[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [newGroup, setNewGroup] = useState({
    groupId: "",
    description: "",
  })
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null)
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const API_URL = "http://localhost:8000/api"
  const token = getToken()
  const client = applyCaseMiddleware(axios.create())

  // Load groups and users from localStorage on component mount
  useEffect(() => {
    const fetchGroups = async () => {
      const { data } = await client.get(`${API_URL}/groups`,
      {
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      })
      setGroups(data)
    }

    fetchGroups()

    const storedUsers = localStorage.getItem("users")
    if (storedUsers) {
      setUsers(JSON.parse(storedUsers))
    }
  }, [])

  // Save groups to localStorage whenever they change
  useEffect(() => {
    if (groups.length > 0) {
      localStorage.setItem("groups", JSON.stringify(groups))
    }
  }, [groups])

  const handleCreateGroup = async () => {
    const { data } = await client.post(`${API_URL}/groups`,
      newGroup,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      })

    console.log(data)
    setGroups([...groups, data])

    // Reset form
    setNewGroup({
      groupId: "",
      description: "",
    })
  }

  const handleDeleteGroup = async (groupId: string) => {
    await client.delete(
      `${API_URL}/groups/${groupId}`,
      {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      })
    setGroups(groups.filter((group) => group.groupId !== groupId))
  }

  const openManageMembers = (group: Group) => {
    setSelectedGroup(group)
    setSelectedUsers([...group.members])
  }

  const handleSaveMembers = async () => {
    if (selectedGroup) {
      const { data } = await client.post(`${API_URL}/groups/${selectedGroup.groupId}/users`,
        {users: selectedUsers},
        {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
        })

      const members = data.members

      setGroups(groups.map((group) => (group.groupId === selectedGroup.groupId ? { ...group, members: members } : group)))
      setSelectedGroup(null)
    }
  }

  const toggleUserSelection = (userId: string) => {
    if (selectedUsers.includes(userId)) {
      setSelectedUsers(selectedUsers.filter((id) => id !== userId))
    } else {
      setSelectedUsers([...selectedUsers, userId])
    }
  }

  console.log(groups)

  const filteredGroups = groups.filter(
    (group) =>
      group.groupId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      group.description.toLowerCase().includes(searchQuery.toLowerCase()),
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="relative w-64">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search groups..."
            className="pl-8"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <Dialog>
          <DialogTrigger asChild>
            <Button>
              <PlusCircle className="mr-2 h-4 w-4" />
              Create Group
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Group</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="name" className="text-right">
                  Group ID
                </Label>
                <Input
                  id="name"
                  value={newGroup.groupId}
                  onChange={(e) => setNewGroup({ ...newGroup, groupId: e.target.value })}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="description" className="text-right">
                  Description
                </Label>
                <Input
                  id="description"
                  value={newGroup.description}
                  onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })}
                  className="col-span-3"
                />
              </div>
            </div>
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </DialogClose>
              <DialogClose asChild>
                <Button type="button" onClick={handleCreateGroup}>
                  Create
                </Button>
              </DialogClose>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Group ID</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Members</TableHead>
              <TableHead className="w-[150px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredGroups.length > 0 ? (
              filteredGroups.map((group) => (
                <TableRow key={group.groupId}>
                  <TableCell className="font-medium">{group.groupId}</TableCell>
                  <TableCell>{group.description}</TableCell>
                  <TableCell>{group.members.length}</TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm" onClick={() => openManageMembers(group)}>
                            <Users className="h-4 w-4 mr-1" />
                            Members
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-md">
                          <DialogHeader>
                            <DialogTitle>Manage Group Members</DialogTitle>
                          </DialogHeader>
                          <div className="py-4">
                            <Card>
                              <CardHeader>
                                <CardTitle>Users</CardTitle>
                                <CardDescription>Select users to add to this group</CardDescription>
                              </CardHeader>
                              <CardContent>
                                <div className="max-h-[300px] overflow-y-auto space-y-2">
                                  {users.map((user) => (
                                    <div key={user.id} className="flex items-center space-x-2">
                                      <Checkbox
                                        id={`user-${user.id}`}
                                        checked={selectedUsers.includes(user.id)}
                                        onCheckedChange={() => toggleUserSelection(user.id)}
                                      />
                                      <Label htmlFor={`user-${user.id}`}>
                                        {user.name} ({user.email})
                                      </Label>
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>
                          </div>
                          <DialogFooter>
                            <DialogClose asChild>
                              <Button type="button" variant="outline">
                                Cancel
                              </Button>
                            </DialogClose>
                            <DialogClose asChild>
                              <Button type="button" onClick={handleSaveMembers}>
                                Save
                              </Button>
                            </DialogClose>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                      <Button variant="ghost" size="sm" onClick={() => handleDeleteGroup(group.groupId)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-4">
                  No groups found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
